"""
URL routing for legacy web views.

Only includes routes for page rendering and form submissions.
All AJAX operations now use the REST API at /api/v1/.
"""

from django.urls import path
from kanban.views import (
    KanbanBoardView,
    AddTaskView,
    AddColumnView,
)

urlpatterns = [
    path('', KanbanBoardView.as_view(), name='kanban_board'),
    path('add-task/', AddTaskView.as_view(), name='add_task'),
    path('add-column/', AddColumnView.as_view(), name='add_column'),
]
