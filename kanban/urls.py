from django.urls import path
from . import views

urlpatterns = [
    path('', views.kanban_board, name='kanban_board'),
    path('add-task/', views.add_task, name='add_task'),
    path('move-task/', views.move_task, name='move_task'),
]