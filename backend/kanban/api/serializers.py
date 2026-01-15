"""
Serializers for the Kanban API.

Handles JSON serialization/deserialization and validation
for Column and Task objects. Includes user-scoped validation.
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter column choices to user's columns only
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            self.fields['column_id'].queryset = Column.objects.filter(user=request.user)
    
    def validate_title(self, value: str) -> str:
        """Ensure title is not just whitespace."""
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Title cannot be empty or whitespace only.")
        return cleaned
    
    def validate_column_id(self, value):
        """Ensure column belongs to the current user."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.user != request.user:
                raise serializers.ValidationError("You can only add tasks to your own columns.")
        return value


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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter column choices to user's columns only
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            self.fields['column_id'].queryset = Column.objects.filter(user=request.user)
    
    def validate_title(self, value: str) -> str:
        """Ensure title is not just whitespace."""
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Title cannot be empty or whitespace only.")
        return cleaned
    
    def validate_column_id(self, value):
        """Ensure column belongs to the current user."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.user != request.user:
                raise serializers.ValidationError("You can only add tasks to your own columns.")
        return value


class TaskMoveSerializer(serializers.Serializer):
    """
    Serializer for moving a task to a different column.
    """
    column_id = serializers.PrimaryKeyRelatedField(queryset=Column.objects.all())
    order = serializers.IntegerField(min_value=0, required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter column choices to user's columns only
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            self.fields['column_id'].queryset = Column.objects.filter(user=request.user)
    
    def validate_column_id(self, value):
        """Ensure target column belongs to the current user."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.user != request.user:
                raise serializers.ValidationError("You can only move tasks to your own columns.")
        return value


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


# Authentication serializers

class UserRegistrationSerializer(serializers.Serializer):
    """Serializer for user registration."""
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    def validate_username(self, value):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data
    
    def create(self, validated_data):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.Serializer):
    """Serializer for user info."""
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
