"""
Legacy web views for the Kanban board HTML interface.

These views handle page rendering and form submissions.
All views require authentication and filter by logged-in user.
All AJAX operations now use the REST API directly.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.middleware.csrf import get_token
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from kanban.models import Task, Column
import logging

logger = logging.getLogger(__name__)


class KanbanBoardView(LoginRequiredMixin, View):
    """Render the main Kanban board with dynamic columns."""
    login_url = '/admin/login/'  # Redirect to admin login for now

    def get(self, request: HttpRequest):
        # Filter columns by the logged-in user
        columns = Column.objects.filter(user=request.user).prefetch_related('tasks')
        
        # If user has no columns, create defaults
        if not columns.exists():
            default_columns = [
                ('Backlog', 1),
                ('Next', 2),
                ('Today', 3),
                ('In Progress', 4),
                ('Done', 5),
            ]
            for name, order in default_columns:
                Column.objects.create(user=request.user, name=name, order=order)
            columns = Column.objects.filter(user=request.user).prefetch_related('tasks')
        
        context = {
            'columns': columns,
        }
        # Ensure CSRF token is set for subsequent API calls
        get_token(request)
        return render(request, 'kanban/board.html', context)


@method_decorator(csrf_protect, name='dispatch')
class AddTaskView(LoginRequiredMixin, View):
    """Create a new Task from form submission."""
    login_url = '/admin/login/'

    def post(self, request: HttpRequest):
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        column_id = request.POST.get('column_id')
        
        if not title:
            logger.warning('Attempted to create task without title')
            return redirect('kanban_board')
        
        # Get column - must belong to current user
        if column_id:
            column = get_object_or_404(Column, id=column_id, user=request.user)
        else:
            column = Column.objects.filter(user=request.user).first()
            if not column:
                logger.error('No columns exist for user %s', request.user.username)
                return redirect('kanban_board')

        # Assign next global order for this user's tasks
        max_order = Task.objects.filter(user=request.user).aggregate(models.Max('order'))['order__max'] or 0
        next_order = max_order + 1

        Task.objects.create(
            user=request.user,
            title=title,
            description=description,
            column=column,
            order=next_order
        )
        logger.info('Created task "%s" in column "%s" for user %s', title, column.name, request.user.username)
        return redirect('kanban_board')


@method_decorator(csrf_protect, name='dispatch')
class AddColumnView(LoginRequiredMixin, View):
    """Create a new column from form submission."""
    login_url = '/admin/login/'
    MAX_COLUMNS = 12

    def post(self, request: HttpRequest):
        name = request.POST.get('name')
        order = request.POST.get('order')
        
        if not name:
            logger.warning('Attempted to create column without name')
            return redirect('kanban_board')
        
        # Check max columns limit for this user
        if Column.objects.filter(user=request.user).count() >= self.MAX_COLUMNS:
            logger.warning('Cannot create column: max limit of %d reached for user %s', self.MAX_COLUMNS, request.user.username)
            return redirect('kanban_board')
        
        # Default order to end of list if not provided
        if not order:
            last_column = Column.objects.filter(user=request.user).last()
            order = (last_column.order + 1) if last_column else 1
        
        Column.objects.create(user=request.user, name=name, order=int(order))
        logger.info('Created column "%s" for user %s', name, request.user.username)
        return redirect('kanban_board')
