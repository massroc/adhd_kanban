from django.contrib import admin
from kanban.models import Column, Task


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'order']
    list_filter = ['user']
    ordering = ['user', 'order']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'column', 'order', 'created_at', 'updated_at']
    list_filter = ['user', 'column', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['user', 'order']
