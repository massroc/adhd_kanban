"""
Unit tests for Column and Task models.
"""

import pytest
from kanban.models import Column, Task
from kanban.tests.factories import ColumnFactory, TaskFactory


@pytest.fixture
def clean_db(db):
    Column.objects.all().delete()


@pytest.mark.django_db
class TestColumnModel:
    
    def test_create_column(self, clean_db):
        column = Column.objects.create(name='Test Column', order=1)
        assert column.name == 'Test Column'
        assert column.order == 1
    
    def test_column_str(self, clean_db):
        column = ColumnFactory(name='My Column')
        assert str(column) == 'My Column'
    
    def test_columns_ordered_by_order(self, clean_db):
        col3 = ColumnFactory(order=3)
        col1 = ColumnFactory(order=1)
        col2 = ColumnFactory(order=2)
        
        columns = list(Column.objects.all())
        assert columns == [col1, col2, col3]


@pytest.mark.django_db
class TestTaskModel:
    
    def test_create_task(self, clean_db):
        column = ColumnFactory()
        task = Task.objects.create(title='Test Task', column=column)
        assert task.title == 'Test Task'
        assert task.column == column
    
    def test_task_str(self, clean_db):
        task = TaskFactory(title='My Task')
        assert str(task) == 'My Task'
    
    def test_task_has_order_field(self, clean_db):
        task = TaskFactory(order=5)
        assert task.order == 5
    
    def test_tasks_ordered_by_order_then_created(self, clean_db):
        column = ColumnFactory()
        task3 = TaskFactory(column=column, order=3)
        task1 = TaskFactory(column=column, order=1)
        task2 = TaskFactory(column=column, order=2)
        
        tasks = list(column.tasks.all())
        assert tasks == [task1, task2, task3]
    
    def test_task_cascade_delete_with_column(self, clean_db):
        column = ColumnFactory()
        TaskFactory.create_batch(3, column=column)
        
        column.delete()
        assert Task.objects.count() == 0


@pytest.mark.django_db
class TestTaskColumnRelationship:
    
    def test_move_task_between_columns(self, clean_db):
        col1 = ColumnFactory()
        col2 = ColumnFactory()
        task = TaskFactory(column=col1)
        
        task.column = col2
        task.save()
        task.refresh_from_db()
        
        assert task.column == col2
    
    def test_global_order_persists_across_columns(self, clean_db):
        col1 = ColumnFactory()
        col2 = ColumnFactory()
        task = TaskFactory(column=col1, order=5)
        
        task.column = col2
        task.save()
        task.refresh_from_db()
        
        assert task.order == 5  # Order preserved
