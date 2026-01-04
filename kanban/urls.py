from django.urls import path
from .views import (
    KanbanBoardView, 
    AddTaskView, 
    MoveTaskView,
    EditTaskView,
    AddColumnView,
    RenameColumnView,
    DeleteColumnView,
    ReorderColumnsView,
    ReorderTasksView,
)

urlpatterns = [
    path('', KanbanBoardView.as_view(), name='kanban_board'),
    path('add-task/', AddTaskView.as_view(), name='add_task'),
    path('move-task/', MoveTaskView.as_view(), name='move_task'),
    path('edit-task/<int:task_id>/', EditTaskView.as_view(), name='edit_task'),
    path('add-column/', AddColumnView.as_view(), name='add_column'),
    path('rename-column/<int:column_id>/', RenameColumnView.as_view(), name='rename_column'),
    path('delete-column/<int:column_id>/', DeleteColumnView.as_view(), name='delete_column'),
    path('reorder-columns/', ReorderColumnsView.as_view(), name='reorder_columns'),
    path('reorder-tasks/', ReorderTasksView.as_view(), name='reorder_tasks'),
]
