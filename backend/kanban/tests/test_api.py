"""
API tests for the Kanban REST API.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from kanban.models import Column, Task
from kanban.tests.factories import UserFactory, ColumnFactory, TaskFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def clean_db(db):
    """Clear all data before each test."""
    Task.objects.all().delete()
    Column.objects.all().delete()


@pytest.fixture
def user(db):
    """Create a test user."""
    return UserFactory()


@pytest.fixture
def auth_client(api_client, user):
    """Return an authenticated API client."""
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


@pytest.fixture
def other_user(db):
    """Create another test user for isolation tests."""
    return UserFactory()


# ============================================================================
# Authentication Tests
# ============================================================================

@pytest.mark.django_db
class TestAuthEndpoints:
    
    def test_register_user(self, api_client):
        response = api_client.post('/api/v1/auth/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert 'token' in response.data
        assert response.data['user']['username'] == 'newuser'
    
    def test_register_creates_default_columns(self, api_client):
        response = api_client.post('/api/v1/auth/register/', {
            'username': 'newuser',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
        })
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify default columns were created
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.get(username='newuser')
        columns = Column.objects.filter(user=user).order_by('order')
        assert columns.count() == 5
        assert list(columns.values_list('name', flat=True)) == [
            'Backlog', 'Next', 'Today', 'In Progress', 'Done'
        ]
    
    def test_register_duplicate_username_fails(self, api_client, user):
        response = api_client.post('/api/v1/auth/register/', {
            'username': user.username,
            'password': 'securepass123',
            'password_confirm': 'securepass123',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_password_mismatch_fails(self, api_client):
        response = api_client.post('/api/v1/auth/register/', {
            'username': 'newuser',
            'password': 'securepass123',
            'password_confirm': 'differentpass',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_login_success(self, api_client, user):
        response = api_client.post('/api/v1/auth/login/', {
            'username': user.username,
            'password': 'testpass123',
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data
    
    def test_login_invalid_credentials(self, api_client, user):
        response = api_client.post('/api/v1/auth/login/', {
            'username': user.username,
            'password': 'wrongpassword',
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_logout(self, auth_client, user):
        response = auth_client.post('/api/v1/auth/logout/')
        assert response.status_code == status.HTTP_200_OK
        assert not Token.objects.filter(user=user).exists()
    
    def test_get_current_user(self, auth_client, user):
        response = auth_client.get('/api/v1/auth/me/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == user.username
    
    def test_unauthenticated_access_denied(self, api_client):
        response = api_client.get('/api/v1/columns/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Column API Tests
# ============================================================================

@pytest.mark.django_db
class TestColumnListEndpoint:
    
    def test_list_columns(self, auth_client, user, clean_db):
        ColumnFactory.create_batch(3, user=user)
        response = auth_client.get('/api/v1/columns/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
    
    def test_columns_isolated_by_user(self, auth_client, user, other_user, clean_db):
        ColumnFactory.create_batch(2, user=user)
        ColumnFactory.create_batch(3, user=other_user)
        
        response = auth_client.get('/api/v1/columns/')
        assert len(response.data['results']) == 2
    
    def test_columns_ordered_by_order_field(self, auth_client, user, clean_db):
        ColumnFactory(name='Third', order=3, user=user)
        ColumnFactory(name='First', order=1, user=user)
        ColumnFactory(name='Second', order=2, user=user)
        
        response = auth_client.get('/api/v1/columns/')
        names = [c['name'] for c in response.data['results']]
        assert names == ['First', 'Second', 'Third']


@pytest.mark.django_db
class TestColumnCreateEndpoint:
    
    def test_create_column(self, auth_client, user, clean_db):
        response = auth_client.post('/api/v1/columns/', {'name': 'New Column'})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Column'
        assert Column.objects.filter(user=user).count() == 1
    
    def test_create_column_empty_name_fails(self, auth_client, clean_db):
        response = auth_client.post('/api/v1/columns/', {'name': ''})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestColumnUpdateEndpoint:
    
    def test_rename_column(self, auth_client, user, clean_db):
        column = ColumnFactory(name='Original', user=user)
        response = auth_client.patch(f'/api/v1/columns/{column.id}/', {'name': 'Renamed'})
        assert response.status_code == status.HTTP_200_OK
        column.refresh_from_db()
        assert column.name == 'Renamed'
    
    def test_cannot_update_other_users_column(self, auth_client, other_user, clean_db):
        column = ColumnFactory(user=other_user)
        response = auth_client.patch(f'/api/v1/columns/{column.id}/', {'name': 'Hacked'})
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestColumnDeleteEndpoint:
    
    def test_delete_column(self, auth_client, user, clean_db):
        column = ColumnFactory(user=user)
        response = auth_client.delete(f'/api/v1/columns/{column.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Column.objects.filter(id=column.id).exists()
    
    def test_delete_column_cascades_tasks(self, auth_client, user, clean_db):
        column = ColumnFactory(user=user)
        TaskFactory.create_batch(3, column=column, user=user)
        
        auth_client.delete(f'/api/v1/columns/{column.id}/')
        assert Task.objects.filter(user=user).count() == 0
    
    def test_cannot_delete_other_users_column(self, auth_client, other_user, clean_db):
        column = ColumnFactory(user=other_user)
        response = auth_client.delete(f'/api/v1/columns/{column.id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Task API Tests
# ============================================================================

@pytest.mark.django_db
class TestTaskListEndpoint:
    
    def test_list_tasks(self, auth_client, user, clean_db):
        column = ColumnFactory(user=user)
        TaskFactory.create_batch(3, column=column, user=user)
        
        response = auth_client.get('/api/v1/tasks/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
    
    def test_tasks_isolated_by_user(self, auth_client, user, other_user, clean_db):
        col1 = ColumnFactory(user=user)
        col2 = ColumnFactory(user=other_user)
        TaskFactory.create_batch(2, column=col1, user=user)
        TaskFactory.create_batch(3, column=col2, user=other_user)
        
        response = auth_client.get('/api/v1/tasks/')
        assert len(response.data['results']) == 2
    
    def test_filter_tasks_by_column(self, auth_client, user, clean_db):
        col1 = ColumnFactory(user=user)
        col2 = ColumnFactory(user=user)
        TaskFactory.create_batch(2, column=col1, user=user)
        TaskFactory.create_batch(3, column=col2, user=user)
        
        response = auth_client.get(f'/api/v1/tasks/?column={col1.id}')
        assert len(response.data['results']) == 2


@pytest.mark.django_db
class TestTaskCreateEndpoint:
    
    def test_create_task(self, auth_client, user, clean_db):
        column = ColumnFactory(user=user)
        response = auth_client.post('/api/v1/tasks/', {
            'title': 'New Task',
            'column_id': column.id
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'New Task'
    
    def test_create_task_empty_title_fails(self, auth_client, user, clean_db):
        column = ColumnFactory(user=user)
        response = auth_client.post('/api/v1/tasks/', {
            'title': '',
            'column_id': column.id
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_task_assigns_global_order(self, auth_client, user, clean_db):
        column = ColumnFactory(user=user)
        TaskFactory(column=column, user=user, order=5)
        
        response = auth_client.post('/api/v1/tasks/', {
            'title': 'New Task',
            'column_id': column.id
        })
        assert response.data['order'] == 6
    
    def test_cannot_create_task_in_other_users_column(self, auth_client, other_user, clean_db):
        column = ColumnFactory(user=other_user)
        response = auth_client.post('/api/v1/tasks/', {
            'title': 'Sneaky Task',
            'column_id': column.id
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTaskUpdateEndpoint:
    
    def test_update_task(self, auth_client, user, clean_db):
        task = TaskFactory(title='Original', user=user)
        response = auth_client.patch(f'/api/v1/tasks/{task.id}/', {
            'title': 'Updated'
        })
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.title == 'Updated'
    
    def test_cannot_update_other_users_task(self, auth_client, other_user, clean_db):
        task = TaskFactory(user=other_user)
        response = auth_client.patch(f'/api/v1/tasks/{task.id}/', {
            'title': 'Hacked'
        })
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestTaskMoveEndpoint:
    
    def test_move_task_to_different_column(self, auth_client, user, clean_db):
        col1 = ColumnFactory(user=user)
        col2 = ColumnFactory(user=user)
        task = TaskFactory(column=col1, user=user)
        
        response = auth_client.post(f'/api/v1/tasks/{task.id}/move/', {
            'column_id': col2.id
        })
        assert response.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.column == col2
    
    def test_move_task_preserves_order(self, auth_client, user, clean_db):
        col1 = ColumnFactory(user=user)
        col2 = ColumnFactory(user=user)
        task = TaskFactory(column=col1, user=user, order=5)
        
        auth_client.post(f'/api/v1/tasks/{task.id}/move/', {
            'column_id': col2.id
        })
        task.refresh_from_db()
        assert task.order == 5
    
    def test_cannot_move_task_to_other_users_column(self, auth_client, user, other_user, clean_db):
        col1 = ColumnFactory(user=user)
        col2 = ColumnFactory(user=other_user)
        task = TaskFactory(column=col1, user=user)
        
        response = auth_client.post(f'/api/v1/tasks/{task.id}/move/', {
            'column_id': col2.id
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTaskDeleteEndpoint:
    
    def test_delete_task(self, auth_client, user, clean_db):
        task = TaskFactory(user=user)
        response = auth_client.delete(f'/api/v1/tasks/{task.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT


# ============================================================================
# Board API Tests
# ============================================================================

@pytest.mark.django_db
class TestBoardEndpoint:
    
    def test_board_returns_columns_with_tasks(self, auth_client, user, clean_db):
        col1 = ColumnFactory(name='Todo', order=1, user=user)
        col2 = ColumnFactory(name='Done', order=2, user=user)
        TaskFactory.create_batch(2, column=col1, user=user)
        TaskFactory.create_batch(1, column=col2, user=user)
        
        response = auth_client.get('/api/v1/board/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['columns']) == 2
        assert len(response.data['columns'][0]['tasks']) == 2
        assert len(response.data['columns'][1]['tasks']) == 1
    
    def test_board_isolated_by_user(self, auth_client, user, other_user, clean_db):
        ColumnFactory(user=user)
        ColumnFactory.create_batch(3, user=other_user)
        
        response = auth_client.get('/api/v1/board/')
        assert len(response.data['columns']) == 1


# ============================================================================
# Reorder API Tests
# ============================================================================

@pytest.mark.django_db
class TestReorderColumnsEndpoint:
    
    def test_reorder_columns(self, auth_client, user, clean_db):
        col1 = ColumnFactory(order=1, user=user)
        col2 = ColumnFactory(order=2, user=user)
        col3 = ColumnFactory(order=3, user=user)
        
        response = auth_client.post('/api/v1/reorder-columns/', {
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
    
    def test_cannot_reorder_other_users_columns(self, auth_client, other_user, clean_db):
        col = ColumnFactory(user=other_user)
        
        response = auth_client.post('/api/v1/reorder-columns/', {
            'column_orders': [{'id': col.id, 'order': 1}]
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestReorderTasksEndpoint:
    
    def test_reorder_tasks(self, auth_client, user, clean_db):
        column = ColumnFactory(user=user)
        task1 = TaskFactory(column=column, user=user, order=1)
        task2 = TaskFactory(column=column, user=user, order=2)
        task3 = TaskFactory(column=column, user=user, order=3)
        
        response = auth_client.post('/api/v1/reorder-tasks/', {
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
    
    def test_cannot_reorder_other_users_tasks(self, auth_client, other_user, clean_db):
        col = ColumnFactory(user=other_user)
        task = TaskFactory(column=col, user=other_user)
        
        response = auth_client.post('/api/v1/reorder-tasks/', {
            'task_orders': [{'id': task.id, 'order': 1}]
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Health Check
# ============================================================================

@pytest.mark.django_db
class TestHealthCheckEndpoint:
    
    def test_health_check(self, api_client):
        response = api_client.get('/api/v1/health/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'healthy'
    
    def test_health_check_no_auth_required(self, api_client):
        # No authentication, should still work
        response = api_client.get('/api/v1/health/')
        assert response.status_code == status.HTTP_200_OK
