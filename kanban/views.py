from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Task
import json

def kanban_board(request):
    """Main kanban board view"""
    todo_tasks = Task.objects.filter(status='todo')
    in_progress_tasks = Task.objects.filter(status='in_progress')
    done_tasks = Task.objects.filter(status='done')
    
    context = {
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'done_tasks': done_tasks,
    }
    return render(request, 'kanban/board.html', context)

def add_task(request):
    """Add a new task"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        if title:
            Task.objects.create(
                title=title,
                description=description,
                status='todo'
            )
    return redirect('kanban_board')

@csrf_exempt
def move_task(request):
    """Move task between columns via AJAX"""
    if request.method == 'POST':
        data = json.loads(request.body)
        task_id = data.get('task_id')
        new_status = data.get('new_status')
        
        task = get_object_or_404(Task, id=task_id)
        if new_status in ['todo', 'in_progress', 'done']:
            task.status = new_status
            task.save()
            return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})