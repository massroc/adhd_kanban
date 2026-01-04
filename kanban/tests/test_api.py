"""
API tests for the Kanban REST API.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from kanban.models import Column, Task
from kanban.tests.factories import ColumnFactory, TaskFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def clean_db(db):
    """Clear default columns before each test."""
    Column.objects.all().delete()


# ============================================================================
# Column API Tests
# ============================================================================

@pytest.mark.django_db
class TestColumnListEndpoint:
    
    def test_list_columns(self, api_client, clean_db):
        ColumnFactory.create_batch(3)
        response = api_client.get('/api/v1/columns/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
    
    def test_columns_ordered_by_order_field(self, api_client, clean_db):
        col3 = ColumnFactory(name='Third', order=3)
        col1 = ColumnFactory(name='First', order=1)
        col2 = ColumnFactory(name='Second', order=2)
        
        response = api_client.get('/api/v1/columns/')
        names = [c['name'] for c in response.data['results']]
        assert names == ['First', 'Second', 'Third']


@pytest.mark.django_db
class TestColumnCreateEndpoint:
    
    def test_create_column(self, api_client, clean_db):
        response = api_client.post('/api/v1/columns/', {'name': 'New Column'})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Column'
        assert Column.objects.count() == 1
    
    def test_create_column_empty_name_fails(self, api_client, clean_db):
        response = api_client.post('/api/v1/columns/', {'name': ''})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestColumnUpdateEndpoint:
    
    def test_rename_column(self, api_client, clean_db):
        column = ColumnFactory(name='Original')
        response = api_client.patch(f'/api/v1/columns/{column.id}/', {'name': 'Renamed'})
        assert response.status_code == status.HTTP_200_OK
        column.refresh_from_db()
        assert column.name == 'Renamed'


@pytest.mark.django_db
class TestColumnDeleteEndpoint:
    
    def test_delete_column(self, api_client, clean_db):
        column = ColumnFactory()
        response = api_client.delete(f'/api/v1/columns/{column.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Column.objects.filter(id=column.id).exists()
    
    def test_delete_column_cascades_tasks(self, api_client, clean_db):
        column = ColumnFactory()
        TaskFactory.create_batch(3, column=column)
        
        api_client.delete(f'/api/v1/columns/{column.id}/')
        assert Task.objects.count() == 0


# ============================================================================
# Task API Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskListEndpoint:
    
    def test_list_tasks(self, api_client, clean_db):
        column = ColumnFactory()
        TaskFactory.create_batch(3, column=column)
        
        response = api_client.get('/api/v1/tasks/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
    
    def test_filter_tasks_by_column(self, api_client, clean_db):
        col1 = ColumnFactory()
        col2 = ColumnFactory()
        TaskFactory.create_batch(2, column=col1)
        TaskFactory.create_batch(3, column=col2)
        
        response = api_client.get(f'/api/v1/tasks/?column={col1.id}')
        assert len(response.data['results']) == 2


@pytest.mark.django_db
class TestTaskCreateEndpoint:
    
    def test_create_task(self, api_client, clean_db):
        column = ColumnFactory()
        response = api_client.post('/api/v1/tasks/', {
            'title': 'New Task',
            'column_id': column.id
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'New Task'
    
    def test_create_task_empty_title_fails(self, api_client, clean_db):
        column = ColumnFactory()
        response = api_client.post('/api/v1/tasks/', {
            'title': '',
            'column_id': column.id
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_task_assigns_global_order(self, api_client, clean_db):
        column = ColumnFactory()
        TaskFactory(column=column, order=5)
        
        response = api_client.post('/api/v1/tasks/', {
            'title': 'New Task',
            'column_id': column.id
        })
        assert response.data['order'] == 6


@pytest.mark.django_db
class TestTaskUpdateEndpoint:
    
    def test_update_task(self, api_client, clean_db):
        task = TaskFactory(title='Original')
        response = api_client.patch(f'/api/v1/tasks/{task.id}/', {
            'title': 'Updated'
        })
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.title == 'Updated'


@pytest.mark.django_db
class TestTaskMoveEndpoint:
    
    def test_move_task_to_different_column(self, api_client, clean_db):
        col1 = ColumnFactory()
        col2 = ColumnFactory()
        task = TaskFactory(column=col1)
        
        response = api_client.post(f'/api/v1/tasks/{task.id}/move/', {
            'column_id': col2.id
        })
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.column == col2
    
    def test_move_task_preserves_order(self, api_client, clean_db):
        col1 = ColumnFactory()
        col2 = ColumnFactory()
        task = TaskFactory(column=col1, order=5)
        
        api_client.post(f'/api/v1/tasks/{task.id}/move/', {
            'column_id': col2.id
        })
        task.refresh_from_db()
        assert task.order == 5


@pytest.mark.django_db
class TestTaskDeleteEndpoint:
    
    def test_delete_task(self, api_client, clean_db):
        task = TaskFactory()
        response = api_client.delete(f'/api/v1/tasks/{task.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT


# ============================================================================
# Board API Tests
# ============================================================================

@pytest.mark.django_db
class TestBoardEndpoint:
    
    def test_board_returns_columns_with_tasks(self, api_client, clean_db):
        col1 = ColumnFactory(name='Todo', order=1)
        col2 = ColumnFactory(name='Done', order=2)
        TaskFactory.create_batch(2, column=col1)
        TaskFactory.create_batch(1, column=col2)
        
        response = api_client.get('/api/v1/board/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['columns']) == 2
        assert len(response.data['columns'][0]['tasks']) == 2
        assert len(response.data['columns'][1]['tasks']) == 1


# ============================================================================
# Reorder API Tests
# ============================================================================

@pytest.mark.django_db
class TestReorderColumnsEndpoint:
    
    def test_reorder_columns(self, api_client, clean_db):
        col1 = ColumnFactory(order=1)
        col2 = ColumnFactory(order=2)
        col3 = ColumnFactory(order=3)
        
        response = api_client.post('/api/v1/reorder-columns/', {
            'column_orders': [
                {'id': col3.id, 'order': 1},
                {'id': col1.id, 'order': 2},
                {'id': col2.id, 'order': 3},
            ]
        })
        assert response.status_code == status.HTTP_200_OK
        
        col1.refresh_from_db()
        col2.refresh_from_db()
        col3.refresh_from_db()
        assert col3.order == 1
        assert col1.order == 2
        assert col2.order == 3


@pytest.mark.django_db
class TestReorderTasksEndpoint:
    
    def test_reorder_tasks(self, api_client, clean_db):
        column = ColumnFactory()
        task1 = TaskFactory(column=column, order=1)
        task2 = TaskFactory(column=column, order=2)
        task3 = TaskFactory(column=column, order=3)
        
        response = api_client.post('/api/v1/reorder-tasks/', {
            'task_orders': [
                {'id': task3.id, 'order': 1},
                {'id': task1.id, 'order': 2},
                {'id': task2.id, 'order': 3},
            ]
        })
        assert response.status_code == status.HTTP_200_OK
        
        task1.refresh_from_db()
        task2.refresh_from_db()
        task3.refresh_from_db()
        assert task3.order == 1
        assert task1.order == 2
        assert task2.order == 3


# ============================================================================
# Health Check
# ============================================================================

@pytest.mark.django_db
class TestHealthCheckEndpoint:
    
    def test_health_check(self, api_client):
        response = api_client.get('/api/v1/health/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'healthy'
