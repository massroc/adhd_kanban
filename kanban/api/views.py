"""
API views for the Kanban board.

Provides REST endpoints for column and task management.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.db import transaction
from django.db.models import Max

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
)

logger = logging.getLogger(__name__)


class ColumnViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Column CRUD operations.
    
    Endpoints:
        GET /api/v1/columns/ - List all columns
        POST /api/v1/columns/ - Create a column
        GET /api/v1/columns/{id}/ - Retrieve a column
        PUT /api/v1/columns/{id}/ - Update a column
        PATCH /api/v1/columns/{id}/ - Partial update
        DELETE /api/v1/columns/{id}/ - Delete a column
    """
    
    queryset = Column.objects.all()
    serializer_class = ColumnSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ColumnCreateSerializer
        return ColumnSerializer
    
    def perform_create(self, serializer):
        """Set order to end of list on create."""
        max_order = Column.objects.aggregate(Max('order'))['order__max'] or 0
        serializer.save(order=max_order + 1)
        logger.info(f"Created column: {serializer.instance.name}")
    
    def perform_destroy(self, instance):
        """Log column deletion."""
        logger.info(f"Deleted column: {instance.name} (id={instance.id})")
        instance.delete()


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Task CRUD operations.
    
    Endpoints:
        GET /api/v1/tasks/ - List all tasks
        POST /api/v1/tasks/ - Create a task
        GET /api/v1/tasks/{id}/ - Retrieve a task
        PUT /api/v1/tasks/{id}/ - Update a task
        PATCH /api/v1/tasks/{id}/ - Partial update
        DELETE /api/v1/tasks/{id}/ - Delete a task
        POST /api/v1/tasks/{id}/move/ - Move task to new column
    """
    
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        if self.action == 'move':
            return TaskMoveSerializer
        return TaskSerializer
    
    def get_queryset(self):
        """
        Optionally filter tasks by column.
        
        Query params:
            column: Filter by column ID
        """
        queryset = Task.objects.all()
        column_id = self.request.query_params.get('column')
        
        if column_id:
            queryset = queryset.filter(column_id=column_id)
        
        return queryset.order_by('order', '-created_at')
    
    def perform_create(self, serializer):
        """Set order to next global order on create."""
        max_order = Task.objects.aggregate(Max('order'))['order__max'] or 0
        serializer.save(order=max_order + 1)
        logger.info(f"Created task: {serializer.instance.title}")
    
    def perform_destroy(self, instance):
        """Log task deletion."""
        logger.info(f"Deleted task: {instance.title} (id={instance.id})")
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
            column_id: Target column ID
            order: Optional new order position
        """
        task = self.get_object()
        serializer = TaskMoveSerializer(data=request.data)
        
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
        
        logger.info(f"Moved task {task.id} from {old_column.name} to {new_column.name}")
        
        return Response(TaskSerializer(task).data)


class BoardView(APIView):
    """
    Get the complete board state with all columns and their tasks.
    """
    
    @extend_schema(
        responses={200: BoardSerializer},
    )
    def get(self, request: Request) -> Response:
        """Return all columns with their tasks."""
        columns = Column.objects.prefetch_related('tasks').all()
        serializer = ColumnWithTasksSerializer(columns, many=True)
        return Response({'columns': serializer.data})


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
        
        with transaction.atomic():
            for item in column_orders:
                Column.objects.filter(id=item['id']).update(order=item['order'])
        
        logger.info(f"Reordered {len(column_orders)} columns")
        
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
        
        with transaction.atomic():
            for item in task_orders:
                Task.objects.filter(id=item['id']).update(order=item['order'])
        
        logger.info(f"Reordered {len(task_orders)} tasks")
        
        return Response({'success': True, 'reordered_count': len(task_orders)})


class HealthCheckView(APIView):
    """
    Health check endpoint for deployment monitoring.
    """
    
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
