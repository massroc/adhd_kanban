from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.middleware.csrf import get_token
from django.db import models
from .models import Task, Column
import json
import logging

logger = logging.getLogger(__name__)


class KanbanBoardView(View):
    """Render the main Kanban board with dynamic columns."""

    def get(self, request: HttpRequest):
        columns = Column.objects.all().prefetch_related('tasks')
        
        context = {
            'columns': columns,
        }
        # Ensure CSRF token is set for subsequent POSTs via form or JS
        get_token(request)
        return render(request, 'kanban/board.html', context)


@method_decorator(csrf_protect, name='dispatch')
class AddTaskView(View):
    """Create a new Task from form submission."""

    def post(self, request: HttpRequest):
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        column_id = request.POST.get('column_id')
        
        if not title:
            logger.warning('Attempted to create task without title')
            return redirect('kanban_board')
        
        # Get column or default to first column (Backlog)
        if column_id:
            column = get_object_or_404(Column, id=column_id)
        else:
            column = Column.objects.first()
            if not column:
                logger.error('No columns exist! Cannot create task.')
                return redirect('kanban_board')

        # Assign next global order
        max_order = Task.objects.aggregate(models.Max('order'))['order__max'] or 0
        next_order = max_order + 1

        Task.objects.create(
            title=title,
            description=description,
            column=column,
            order=next_order
        )
        logger.info('Created task "%s" in column "%s" with global order %d', title, column.name, next_order)
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
        column_id = data.get('column_id')

        if not task_id or not column_id:
            return JsonResponse({'success': False, 'error': 'invalid_payload'}, status=400)

        task = get_object_or_404(Task, id=task_id)
        column = get_object_or_404(Column, id=column_id)
        
        task.column = column
        task.save(update_fields=['column', 'updated_at'])
        logger.info('Moved task %s to column %s', task.id, column.name)
        return JsonResponse({'success': True})


@method_decorator(csrf_protect, name='dispatch')
class EditTaskView(View):
    """Edit an existing task's title and description."""

    def post(self, request: HttpRequest, task_id: int):
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            logger.exception('Invalid JSON payload in edit_task')
            return HttpResponseBadRequest('Invalid JSON')

        title = data.get('title', '').strip()
        description = data.get('description', '').strip()

        if not title:
            return JsonResponse({'success': False, 'error': 'title_required'}, status=400)

        task = get_object_or_404(Task, id=task_id)
        task.title = title
        task.description = description
        task.save(update_fields=['title', 'description', 'updated_at'])
        
        logger.info('Edited task %s: "%s"', task.id, title)
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
            }
        })


@method_decorator(csrf_protect, name='dispatch')
class AddColumnView(View):
    """Create a new column."""
    
    MAX_COLUMNS = 12

    def post(self, request: HttpRequest):
        name = request.POST.get('name')
        order = request.POST.get('order')
        
        if not name:
            logger.warning('Attempted to create column without name')
            return redirect('kanban_board')
        
        # Check max columns limit
        if Column.objects.count() >= self.MAX_COLUMNS:
            logger.warning('Cannot create column: max limit of %d reached', self.MAX_COLUMNS)
            return redirect('kanban_board')
        
        # Default order to end of list if not provided
        if not order:
            last_column = Column.objects.last()
            order = (last_column.order + 1) if last_column else 1
        
        Column.objects.create(name=name, order=int(order))
        logger.info('Created column "%s" with order %s', name, order)
        return redirect('kanban_board')


@method_decorator(csrf_protect, name='dispatch')
class RenameColumnView(View):
    """Rename an existing column."""

    def post(self, request: HttpRequest, column_id: int):
        name = request.POST.get('name')
        
        if not name:
            logger.warning('Attempted to rename column without providing name')
            return redirect('kanban_board')
        
        column = get_object_or_404(Column, id=column_id)
        old_name = column.name
        column.name = name
        column.save(update_fields=['name'])
        logger.info('Renamed column from "%s" to "%s"', old_name, name)
        return redirect('kanban_board')


@method_decorator(csrf_protect, name='dispatch')
class DeleteColumnView(View):
    """Delete a column and move its tasks to the first column."""

    def post(self, request: HttpRequest, column_id: int):
        # Prevent deleting the last column
        if Column.objects.count() <= 1:
            logger.warning('Cannot delete last remaining column')
            return redirect('kanban_board')
        
        column = get_object_or_404(Column, id=column_id)
        
        # Move tasks to first column (by order)
        first_column = Column.objects.exclude(id=column_id).first()
        tasks_to_move = column.tasks.all()
        tasks_to_move.update(column=first_column)
        
        logger.info('Moved %d tasks from column "%s" to "%s"', 
                   tasks_to_move.count(), column.name, first_column.name)
        
        column.delete()
        logger.info('Deleted column "%s"', column.name)
        return redirect('kanban_board')


@method_decorator(csrf_protect, name='dispatch')
class ReorderColumnsView(View):
    """Reorder columns via drag and drop."""

    def post(self, request: HttpRequest):
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            logger.exception('Invalid JSON payload in reorder_columns')
            return HttpResponseBadRequest('Invalid JSON')

        column_orders = data.get('column_orders', [])
        
        if not column_orders:
            return JsonResponse({'success': False, 'error': 'no_data'}, status=400)
        
        # Update each column's order
        for item in column_orders:
            column_id = item.get('id')
            new_order = item.get('order')
            
            if column_id and new_order is not None:
                Column.objects.filter(id=column_id).update(order=new_order)
        
        logger.info('Reordered %d columns', len(column_orders))
        return JsonResponse({'success': True})


@method_decorator(csrf_protect, name='dispatch')
class ReorderTasksView(View):
    """Reorder tasks with global priority that persists across columns."""

    def post(self, request: HttpRequest):
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            logger.exception('Invalid JSON payload in reorder_tasks')
            return HttpResponseBadRequest('Invalid JSON')

        task_orders = data.get('task_orders', [])
        column_id = data.get('column_id')
        
        if not task_orders or not column_id:
            return JsonResponse({'success': False, 'error': 'no_data'}, status=400)
        
        # Build a map of task_id -> new position in column
        task_position_map = {str(item['id']): item['order'] for item in task_orders}
        reordered_task_ids = set(task_position_map.keys())
        
        # Get all tasks globally ordered
        all_tasks = list(Task.objects.all().order_by('order', 'id'))
        
        # Split tasks into:
        # 1. Tasks from this column (in their new order)
        # 2. Tasks from other columns (keep original order)
        tasks_in_column = []
        tasks_other_columns = []
        
        for task in all_tasks:
            if str(task.id) in reordered_task_ids:
                tasks_in_column.append(task)
            else:
                tasks_other_columns.append(task)
        
        # Sort tasks in column by their new visual order
        tasks_in_column.sort(key=lambda t: task_position_map[str(t.id)])
        
        # Find where to insert the column's tasks in the global order
        # Insert them at the position of the first task that was in this column
        first_column_task_global_pos = None
        for i, task in enumerate(all_tasks):
            if str(task.id) in reordered_task_ids:
                first_column_task_global_pos = i
                break
        
        # Rebuild the global task list
        if first_column_task_global_pos is not None:
            # Remove all column tasks from other_columns (they shouldn't be there anyway)
            # and insert the reordered column tasks at the original position
            new_global_order = []
            column_tasks_inserted = False
            
            for i, task in enumerate(all_tasks):
                if str(task.id) in reordered_task_ids:
                    # Insert all column tasks at the position of the first one
                    if not column_tasks_inserted:
                        new_global_order.extend(tasks_in_column)
                        column_tasks_inserted = True
                else:
                    new_global_order.append(task)
        else:
            # Shouldn't happen, but fallback
            new_global_order = tasks_other_columns + tasks_in_column
        
        # Renumber all tasks with their new global order
        for index, task in enumerate(new_global_order, start=1):
            if task.order != index:
                task.order = index
                task.save(update_fields=['order'])
        
        logger.info('Reordered tasks in column %s, updated global ordering', column_id)
        return JsonResponse({'success': True})
