"""
Unit tests for Column and Task models.
"""

import pytest
from kanban.models import Column, Task
from kanban.tests.factories import UserFactory, ColumnFactory, TaskFactory


@pytest.fixture
def clean_db(db):
    Task.objects.all().delete()
    Column.objects.all().delete()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.mark.django_db
class TestColumnModel:
    
    def test_create_column(self, clean_db, user):
        column = Column.objects.create(name='Test Column', order=1, user=user)
        assert column.name == 'Test Column'
        assert column.order == 1
        assert column.user == user
    
    def test_column_str(self, clean_db, user):
        column = ColumnFactory(name='My Column', user=user)
        assert str(column) == 'My Column'
    
    def test_columns_ordered_by_order(self, clean_db, user):
        col3 = ColumnFactory(order=3, user=user)
        col1 = ColumnFactory(order=1, user=user)
        col2 = ColumnFactory(order=2, user=user)
        
        columns = list(Column.objects.filter(user=user))
        assert columns == [col1, col2, col3]


@pytest.mark.django_db
class TestTaskModel:
    
    def test_create_task(self, clean_db, user):
        column = ColumnFactory(user=user)
        task = Task.objects.create(title='Test Task', column=column, user=user)
        assert task.title == 'Test Task'
        assert task.column == column
        assert task.user == user
    
    def test_task_str(self, clean_db):
        task = TaskFactory(title='My Task')
        assert str(task) == 'My Task'
    
    def test_task_has_order_field(self, clean_db):
        task = TaskFactory(order=5)
        assert task.order == 5
    
    def test_tasks_ordered_by_order_then_created(self, clean_db, user):
        column = ColumnFactory(user=user)
        task3 = TaskFactory(column=column, user=user, order=3)
        task1 = TaskFactory(column=column, user=user, order=1)
        task2 = TaskFactory(column=column, user=user, order=2)
        
        tasks = list(column.tasks.all())
        assert tasks == [task1, task2, task3]
    
    def test_task_cascade_delete_with_column(self, clean_db, user):
        column = ColumnFactory(user=user)
        TaskFactory.create_batch(3, column=column, user=user)
        
        column.delete()
        assert Task.objects.filter(user=user).count() == 0


@pytest.mark.django_db
class TestTaskColumnRelationship:
    
    def test_move_task_between_columns(self, clean_db, user):
        col1 = ColumnFactory(user=user)
        col2 = ColumnFactory(user=user)
        task = TaskFactory(column=col1, user=user)
        
        task.column = col2
        task.save()
        task.refresh_from_db()
        
        assert task.column == col2
    
    def test_global_order_persists_across_columns(self, clean_db, user):
        col1 = ColumnFactory(user=user)
        col2 = ColumnFactory(user=user)
        task = TaskFactory(column=col1, user=user, order=5)
        
        task.column = col2
        task.save()
        task.refresh_from_db()
        
        assert task.order == 5  # Order preserved


@pytest.mark.django_db
class TestUserIsolation:
    """Tests to verify data isolation between users."""
    
    def test_columns_belong_to_user(self, clean_db):
        user1 = UserFactory()
        user2 = UserFactory()
        
        col1 = ColumnFactory(user=user1)
        col2 = ColumnFactory(user=user2)
        
        assert col1.user == user1
        assert col2.user == user2
        assert Column.objects.filter(user=user1).count() == 1
        assert Column.objects.filter(user=user2).count() == 1
    
    def test_tasks_belong_to_user(self, clean_db):
        user1 = UserFactory()
        user2 = UserFactory()
        
        col1 = ColumnFactory(user=user1)
        col2 = ColumnFactory(user=user2)
        
        task1 = TaskFactory(column=col1, user=user1)
        task2 = TaskFactory(column=col2, user=user2)
        
        assert task1.user == user1
        assert task2.user == user2
        assert Task.objects.filter(user=user1).count() == 1
        assert Task.objects.filter(user=user2).count() == 1
    
    def test_user_deletion_cascades_to_columns_and_tasks(self, clean_db):
        user = UserFactory()
        col = ColumnFactory(user=user)
        TaskFactory.create_batch(3, column=col, user=user)
        
        user.delete()
        
        assert Column.objects.count() == 0
        assert Task.objects.count() == 0
