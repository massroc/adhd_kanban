"""
URL routing for the Kanban API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from kanban.api.views import (
    ColumnViewSet,
    TaskViewSet,
    BoardView,
    ReorderColumnsView,
    ReorderTasksView,
    HealthCheckView,
)

router = DefaultRouter()
router.register(r'columns', ColumnViewSet, basename='column')
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    # ViewSet routes (CRUD)
    path('', include(router.urls)),
    
    # Custom endpoints
    path('board/', BoardView.as_view(), name='board'),
    path('reorder-columns/', ReorderColumnsView.as_view(), name='reorder-columns'),
    path('reorder-tasks/', ReorderTasksView.as_view(), name='reorder-tasks'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
]
