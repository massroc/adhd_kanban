from django.contrib import admin
from kanban.models import Column, Task


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    ordering = ['order']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'column', 'order', 'created_at', 'updated_at']
    list_filter = ['column', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['order']
