"""
Legacy web views for the Kanban board HTML interface.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.middleware.csrf import get_token
from django.db.models import Max
from kanban.models import Column, Task
import json
import logging

logger = logging.getLogger(__name__)


class KanbanBoardView(View):
    """Render the main Kanban board."""

    def get(self, request: HttpRequest):
        columns = Column.objects.prefetch_related('tasks').all()
        get_token(request)
        return render(request, 'kanban/board.html', {'columns': columns})


@method_decorator(csrf_protect, name='dispatch')
class AddTaskView(View):
    """Create a new Task."""

    def post(self, request: HttpRequest):
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        column_id = request.POST.get('column_id')
        
        if not title or not column_id:
            logger.warning('Attempted to create task without title or column')
            return redirect('kanban_board')

        column = get_object_or_404(Column, id=column_id)
        max_order = Task.objects.aggregate(Max('order'))['order__max'] or 0
        
        Task.objects.create(
            title=title,
            description=description,
            column=column,
            order=max_order + 1
        )
        return redirect('kanban_board')


@method_decorator(csrf_protect, name='dispatch')
class MoveTaskView(View):
    """Move task between columns."""

    def post(self, request: HttpRequest):
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON')

        task_id = data.get('task_id')
        column_id = data.get('column_id')

        if not task_id or not column_id:
            return JsonResponse({'success': False, 'error': 'invalid_payload'}, status=400)

        task = get_object_or_404(Task, id=task_id)
        column = get_object_or_404(Column, id=column_id)
        
        task.column = column
        task.save(update_fields=['column', 'updated_at'])
        logger.info('Moved task %s to %s', task.id, column.name)
        return JsonResponse({'success': True})


@method_decorator(csrf_protect, name='dispatch')
class EditTaskView(View):
    """Edit an existing task."""

    def post(self, request: HttpRequest):
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON')

        task_id = data.get('task_id')
        title = data.get('title')
        description = data.get('description', '')

        if not task_id or not title:
            return JsonResponse({'success': False, 'error': 'invalid_payload'}, status=400)

        task = get_object_or_404(Task, id=task_id)
        task.title = title
        task.description = description
        task.save(update_fields=['title', 'description', 'updated_at'])
        
        return JsonResponse({'success': True})


@method_decorator(csrf_protect, name='dispatch')
class ReorderTasksView(View):
    """Reorder tasks within columns."""

    def post(self, request: HttpRequest):
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON')

        task_orders = data.get('task_orders', [])

        for item in task_orders:
            Task.objects.filter(id=item['id']).update(order=item['order'])

        return JsonResponse({'success': True})


@method_decorator(csrf_protect, name='dispatch')
class AddColumnView(View):
    """Create a new column."""

    def post(self, request: HttpRequest):
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON')

        name = data.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'name_required'}, status=400)

        max_order = Column.objects.aggregate(Max('order'))['order__max'] or 0
        column = Column.objects.create(name=name, order=max_order + 1)

        return JsonResponse({
            'success': True,
            'column': {'id': column.id, 'name': column.name, 'order': column.order}
        })


@method_decorator(csrf_protect, name='dispatch')
class RenameColumnView(View):
    """Rename an existing column."""

    def post(self, request: HttpRequest):
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON')

        column_id = data.get('column_id')
        name = data.get('name', '').strip()

        if not column_id or not name:
            return JsonResponse({'success': False, 'error': 'invalid_payload'}, status=400)

        column = get_object_or_404(Column, id=column_id)
        column.name = name
        column.save(update_fields=['name'])

        return JsonResponse({'success': True})


@method_decorator(csrf_protect, name='dispatch')
class DeleteColumnView(View):
    """Delete a column (and all its tasks)."""

    def post(self, request: HttpRequest):
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON')

        column_id = data.get('column_id')
        if not column_id:
            return JsonResponse({'success': False, 'error': 'column_id_required'}, status=400)

        column = get_object_or_404(Column, id=column_id)
        column.delete()

        return JsonResponse({'success': True})


@method_decorator(csrf_protect, name='dispatch')
class ReorderColumnsView(View):
    """Reorder columns."""

    def post(self, request: HttpRequest):
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            return HttpResponseBadRequest('Invalid JSON')

        column_orders = data.get('column_orders', [])

        for item in column_orders:
            Column.objects.filter(id=item['id']).update(order=item['order'])

        return JsonResponse({'success': True})
