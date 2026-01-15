"""
Models for the Kanban board.

The board uses a Column model for flexible column management,
with Tasks belonging to Columns via ForeignKey.
Each user has their own set of columns and tasks.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class Column(models.Model):
    """
    Represents a column on the Kanban board.
    
    Columns can be created, renamed, deleted, and reordered.
    Each user has their own set of columns.
    Default columns: Backlog, Next, Today, In Progress, Done
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='columns'
    )
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0, db_index=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self) -> str:
        return self.name


class Task(models.Model):
    """
    Represents a task card on the Kanban board.
    
    Tasks belong to a Column and have a global order for priority.
    The order field maintains priority even when tasks move between columns.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    column = models.ForeignKey(
        Column,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    order = models.IntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
    
    def __str__(self) -> str:
        return self.title
