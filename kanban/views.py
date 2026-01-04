"""
Legacy web views for the Kanban board HTML interface.

These views handle page rendering and form submissions.
All AJAX operations now use the REST API directly.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.middleware.csrf import get_token
from django.db import models
from kanban.models import Task, Column
import logging

logger = logging.getLogger(__name__)


class KanbanBoardView(View):
    """Render the main Kanban board with dynamic columns."""

    def get(self, request: HttpRequest):
        columns = Column.objects.all().prefetch_related('tasks')
        
        context = {
            'columns': columns,
        }
        # Ensure CSRF token is set for subsequent API calls
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
class AddColumnView(View):
    """Create a new column from form submission."""
    
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
