"""
API views for the Kanban board.

Provides REST endpoints for column and task management.
All endpoints filter data by authenticated user.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.db import transaction
from django.db.models import Max
from django.contrib.auth import authenticate

from kanban.models import Column, Task
from kanban.api.serializers import (
    ColumnSerializer,
    ColumnCreateSerializer,
    ColumnReorderSerializer,
    ColumnWithTasksSerializer,
    TaskSerializer,
    TaskCreateSerializer,
    TaskMoveSerializer,
    TaskReorderSerializer,
    BoardSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Authentication Views
# =============================================================================

class RegisterView(APIView):
    """
    Register a new user account.
    Creates default columns for the new user.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        request=UserRegistrationSerializer,
        responses={
            201: OpenApiResponse(description="User created successfully"),
            400: OpenApiResponse(description="Invalid registration data"),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = UserRegistrationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save()
        
        # Create default columns for the new user
        default_columns = [
            ('Backlog', 1),
            ('Next', 2),
            ('Today', 3),
            ('In Progress', 4),
            ('Done', 5),
        ]
        for name, order in default_columns:
            Column.objects.create(user=user, name=name, order=order)
        
        # Create auth token
        token, _ = Token.objects.get_or_create(user=user)
        
        logger.info(f"New user registered: {user.username}")
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Authenticate user and return token.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        request=UserLoginSerializer,
        responses={
            200: OpenApiResponse(description="Login successful"),
            401: OpenApiResponse(description="Invalid credentials"),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = UserLoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        
        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        token, _ = Token.objects.get_or_create(user=user)
        
        logger.info(f"User logged in: {user.username}")
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
        })


class LogoutView(APIView):
    """
    Logout user by deleting their token.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: OpenApiResponse(description="Logged out successfully")},
    )
    def post(self, request: Request) -> Response:
        # Delete the user's token
        Token.objects.filter(user=request.user).delete()
        logger.info(f"User logged out: {request.user.username}")
        return Response({'message': 'Logged out successfully'})


class CurrentUserView(APIView):
    """
    Get current authenticated user info.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: UserSerializer},
    )
    def get(self, request: Request) -> Response:
        return Response(UserSerializer(request.user).data)


# =============================================================================
# Column Views
# =============================================================================

class ColumnViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Column CRUD operations.
    
    All operations are scoped to the authenticated user's columns.
    
    Endpoints:
        GET /api/v1/columns/ - List user's columns
        POST /api/v1/columns/ - Create a column
        GET /api/v1/columns/{id}/ - Retrieve a column
        PUT /api/v1/columns/{id}/ - Update a column
        PATCH /api/v1/columns/{id}/ - Partial update
        DELETE /api/v1/columns/{id}/ - Delete a column
    """
    
    serializer_class = ColumnSerializer
    
    def get_queryset(self):
        """Return only columns belonging to the current user."""
        return Column.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ColumnCreateSerializer
        return ColumnSerializer
    
    def perform_create(self, serializer):
        """Set order to end of list and assign user on create."""
        max_order = Column.objects.filter(user=self.request.user).aggregate(Max('order'))['order__max'] or 0
        serializer.save(user=self.request.user, order=max_order + 1)
        logger.info(f"Created column: {serializer.instance.name} for user {self.request.user.username}")
    
    def perform_destroy(self, instance):
        """Log column deletion."""
        logger.info(f"Deleted column: {instance.name} (id={instance.id}) for user {self.request.user.username}")
        instance.delete()


# =============================================================================
# Task Views
# =============================================================================

class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Task CRUD operations.
    
    All operations are scoped to the authenticated user's tasks.
    
    Endpoints:
        GET /api/v1/tasks/ - List user's tasks
        POST /api/v1/tasks/ - Create a task
        GET /api/v1/tasks/{id}/ - Retrieve a task
        PUT /api/v1/tasks/{id}/ - Update a task
        PATCH /api/v1/tasks/{id}/ - Partial update
        DELETE /api/v1/tasks/{id}/ - Delete a task
        POST /api/v1/tasks/{id}/move/ - Move task to new column
    """
    
    serializer_class = TaskSerializer
    
    def get_queryset(self):
        """
        Return only tasks belonging to the current user.
        Optionally filter by column.
        """
        queryset = Task.objects.filter(user=self.request.user)
        column_id = self.request.query_params.get('column')
        
        if column_id:
            queryset = queryset.filter(column_id=column_id)
        
        return queryset.order_by('order', '-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        if self.action == 'move':
            return TaskMoveSerializer
        return TaskSerializer
    
    def perform_create(self, serializer):
        """Set order to next global order and assign user on create."""
        max_order = Task.objects.filter(user=self.request.user).aggregate(Max('order'))['order__max'] or 0
        serializer.save(user=self.request.user, order=max_order + 1)
        logger.info(f"Created task: {serializer.instance.title} for user {self.request.user.username}")
    
    def perform_destroy(self, instance):
        """Log task deletion."""
        logger.info(f"Deleted task: {instance.title} (id={instance.id}) for user {self.request.user.username}")
        instance.delete()
    
    @extend_schema(
        request=TaskMoveSerializer,
        responses={
            200: TaskSerializer,
            400: OpenApiResponse(description="Invalid move request"),
            404: OpenApiResponse(description="Task not found"),
        },
    )
    @action(detail=True, methods=['post'])
    def move(self, request: Request, pk=None) -> Response:
        """
        Move a task to a different column.
        
        Accepts:
            column_id: Target column ID (must belong to current user)
            order: Optional new order position
        """
        task = self.get_object()
        serializer = TaskMoveSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_column = task.column
        new_column = serializer.validated_data['column_id']
        new_order = serializer.validated_data.get('order')
        
        task.column = new_column
        if new_order is not None:
            task.order = new_order
        task.save(update_fields=['column', 'order', 'updated_at'])
        
        logger.info(f"Moved task {task.id} from {old_column.name} to {new_column.name} for user {request.user.username}")
        
        return Response(TaskSerializer(task, context={'request': request}).data)


# =============================================================================
# Board Views
# =============================================================================

class BoardView(APIView):
    """
    Get the complete board state with all columns and their tasks.
    """
    
    @extend_schema(
        responses={200: BoardSerializer},
    )
    def get(self, request: Request) -> Response:
        """Return all columns with their tasks for the current user."""
        columns = Column.objects.filter(user=request.user).prefetch_related('tasks')
        serializer = ColumnWithTasksSerializer(columns, many=True, context={'request': request})
        return Response({'columns': serializer.data})


# =============================================================================
# Reorder Views
# =============================================================================

class ReorderColumnsView(APIView):
    """
    Reorder columns via drag and drop.
    """
    
    @extend_schema(
        request=ColumnReorderSerializer,
        responses={
            200: OpenApiResponse(description="Columns reordered successfully"),
            400: OpenApiResponse(description="Invalid request"),
        },
    )
    def post(self, request: Request) -> Response:
        """
        Update order for multiple columns.
        Only affects columns belonging to the current user.
        
        Accepts:
            column_orders: List of {id, order} objects
        """
        serializer = ColumnReorderSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        column_orders = serializer.validated_data['column_orders']
        column_ids = [item['id'] for item in column_orders]
        
        # Verify all columns belong to the current user
        user_column_ids = set(
            Column.objects.filter(user=request.user, id__in=column_ids).values_list('id', flat=True)
        )
        if set(column_ids) != user_column_ids:
            return Response(
                {'error': 'You can only reorder your own columns'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        with transaction.atomic():
            for item in column_orders:
                Column.objects.filter(id=item['id'], user=request.user).update(order=item['order'])
        
        logger.info(f"Reordered {len(column_orders)} columns for user {request.user.username}")
        
        return Response({'success': True, 'reordered_count': len(column_orders)})


class ReorderTasksView(APIView):
    """
    Reorder tasks within or across columns.
    """
    
    @extend_schema(
        request=TaskReorderSerializer,
        responses={
            200: OpenApiResponse(description="Tasks reordered successfully"),
            400: OpenApiResponse(description="Invalid request"),
        },
    )
    def post(self, request: Request) -> Response:
        """
        Update order for multiple tasks.
        Only affects tasks belonging to the current user.
        
        Accepts:
            task_orders: List of {id, order} objects
        """
        serializer = TaskReorderSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task_orders = serializer.validated_data['task_orders']
        task_ids = [item['id'] for item in task_orders]
        
        # Verify all tasks belong to the current user
        user_task_ids = set(
            Task.objects.filter(user=request.user, id__in=task_ids).values_list('id', flat=True)
        )
        if set(task_ids) != user_task_ids:
            return Response(
                {'error': 'You can only reorder your own tasks'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        with transaction.atomic():
            for item in task_orders:
                Task.objects.filter(id=item['id'], user=request.user).update(order=item['order'])
        
        logger.info(f"Reordered {len(task_orders)} tasks for user {request.user.username}")
        
        return Response({'success': True, 'reordered_count': len(task_orders)})


# =============================================================================
# Health Check
# =============================================================================

class HealthCheckView(APIView):
    """
    Health check endpoint for deployment monitoring.
    No authentication required.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        responses={200: OpenApiResponse(description="Service is healthy")},
    )
    def get(self, request: Request) -> Response:
        """Return service health status."""
        return Response({
            'status': 'healthy',
            'service': 'kanban-api',
            'version': '1.0.0',
        })
