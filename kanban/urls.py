from django.urls import path
from .views import KanbanBoardView, AddTaskView, MoveTaskView

urlpatterns = [
    path('', KanbanBoardView.as_view(), name='kanban_board'),
    path('add-task/', AddTaskView.as_view(), name='add_task'),
    path('move-task/', MoveTaskView.as_view(), name='move_task'),
]