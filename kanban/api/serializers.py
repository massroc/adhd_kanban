"""
Serializers for the Kanban API.

Handles JSON serialization/deserialization and validation
for Column and Task objects.
"""

from rest_framework import serializers
from kanban.models import Column, Task


class TaskSerializer(serializers.ModelSerializer):
    """
    Full serializer for Task CRUD operations.
    """
    column_id = serializers.PrimaryKeyRelatedField(
        queryset=Column.objects.all(),
        source='column',
        write_only=True
    )
    column_name = serializers.CharField(source='column.name', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'column',
            'column_id',
            'column_name',
            'order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'column', 'created_at', 'updated_at']
    
    def validate_title(self, value: str) -> str:
        """Ensure title is not just whitespace."""
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Title cannot be empty or whitespace only.")
        return cleaned


class TaskCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new tasks.
    """
    column_id = serializers.PrimaryKeyRelatedField(
        queryset=Column.objects.all(),
        source='column',
        write_only=True
    )
    column = serializers.PrimaryKeyRelatedField(read_only=True)
    column_name = serializers.CharField(source='column.name', read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'column', 'column_id', 'column_name', 'order', 'created_at', 'updated_at']
        read_only_fields = ['id', 'column', 'column_name', 'created_at', 'updated_at']
        extra_kwargs = {
            'order': {'required': False},
        }
    
    def validate_title(self, value: str) -> str:
        """Ensure title is not just whitespace."""
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Title cannot be empty or whitespace only.")
        return cleaned


class TaskMoveSerializer(serializers.Serializer):
    """
    Serializer for moving a task to a different column.
    """
    column_id = serializers.PrimaryKeyRelatedField(queryset=Column.objects.all())
    order = serializers.IntegerField(min_value=0, required=False)


class TaskReorderSerializer(serializers.Serializer):
    """
    Serializer for reordering tasks within a column.
    """
    task_orders = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        ),
        min_length=1
    )
    
    def validate_task_orders(self, value):
        """Validate that each item has id and order keys."""
        for item in value:
            if 'id' not in item or 'order' not in item:
                raise serializers.ValidationError(
                    "Each item must have 'id' and 'order' keys."
                )
        return value


class ColumnSerializer(serializers.ModelSerializer):
    """
    Serializer for Column CRUD operations.
    """
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Column
        fields = ['id', 'name', 'order', 'task_count']
        read_only_fields = ['id']
    
    def get_task_count(self, obj) -> int:
        return obj.tasks.count()
    
    def validate_name(self, value: str) -> str:
        """Ensure name is not just whitespace."""
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Column name cannot be empty.")
        return cleaned


class ColumnCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new columns.
    """
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Column
        fields = ['id', 'name', 'order', 'task_count']
        read_only_fields = ['id', 'task_count']
        extra_kwargs = {
            'order': {'required': False},
        }
    
    def get_task_count(self, obj) -> int:
        return obj.tasks.count()
    
    def validate_name(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Column name cannot be empty.")
        return cleaned


class ColumnReorderSerializer(serializers.Serializer):
    """
    Serializer for reordering columns.
    """
    column_orders = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        ),
        min_length=1
    )
    
    def validate_column_orders(self, value):
        """Validate that each item has id and order keys."""
        for item in value:
            if 'id' not in item or 'order' not in item:
                raise serializers.ValidationError(
                    "Each item must have 'id' and 'order' keys."
                )
        return value


class ColumnWithTasksSerializer(serializers.ModelSerializer):
    """
    Serializer for Column with nested tasks.
    Used for the board endpoint.
    """
    tasks = TaskSerializer(many=True, read_only=True)
    
    class Meta:
        model = Column
        fields = ['id', 'name', 'order', 'tasks']


class BoardSerializer(serializers.Serializer):
    """
    Serializer for the complete board state.
    Returns all columns with their tasks.
    """
    columns = ColumnWithTasksSerializer(many=True)
