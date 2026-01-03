from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.middleware.csrf import get_token
from .models import Task
import json
import logging

logger = logging.getLogger(__name__)

class KanbanBoardView(View):
    """Render the main Kanban board with grouped tasks."""

    def get(self, request: HttpRequest):
        todo_tasks = Task.objects.filter(status='todo')
        in_progress_tasks = Task.objects.filter(status='in_progress')
        done_tasks = Task.objects.filter(status='done')

        context = {
            'todo_tasks': todo_tasks,
            'in_progress_tasks': in_progress_tasks,
            'done_tasks': done_tasks,
        }
        # Ensure CSRF token is set for subsequent POSTs via form or JS
        get_token(request)
        return render(request, 'kanban/board.html', context)

@method_decorator(csrf_protect, name='dispatch')
class AddTaskView(View):
    """Create a new Task from form submission."""
    
    VALID_STATUSES = ['todo', 'in_progress', 'done']

    def post(self, request: HttpRequest):
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        status = request.POST.get('status', 'todo')
        
        if not title:
            logger.warning('Attempted to create task without title')
            return redirect('kanban_board')
        
        # Validate status - default to 'todo' if invalid
        if status not in self.VALID_STATUSES:
            logger.warning('Invalid status "%s" provided, defaulting to todo', status)
            status = 'todo'

        Task.objects.create(
            title=title,
            description=description,
            status=status
        )
        logger.info('Created task "%s" with status "%s"', title, status)
        return redirect('kanban_board')

@method_decorator(csrf_protect, name='dispatch')
class MoveTaskView(View):
    """Move task between columns via JSON POST."""

    def post(self, request: HttpRequest):
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            logger.exception('Invalid JSON payload in move_task')
            return HttpResponseBadRequest('Invalid JSON')

        task_id = data.get('task_id')
        new_status = data.get('new_status')

        if not task_id or new_status not in ['todo', 'in_progress', 'done']:
            return JsonResponse({'success': False, 'error': 'invalid_payload'}, status=400)

        task = get_object_or_404(Task, id=task_id)
        task.status = new_status
        task.save(update_fields=['status', 'updated_at'])
        logger.info('Moved task %s to %s', task.id, new_status)
        return JsonResponse({'success': True})
