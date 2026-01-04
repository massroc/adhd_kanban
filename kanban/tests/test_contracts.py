"""
Contract tests for the Kanban API.

These tests verify API responses match expected schemas.
"""

import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from jsonschema import validate
from kanban.models import Column, Task
from kanban.tests.factories import UserFactory, ColumnFactory, TaskFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def clean_db(db):
    Task.objects.all().delete()
    Column.objects.all().delete()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(api_client, user):
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


# Schema definitions
COLUMN_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "order", "task_count"],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string", "minLength": 1},
        "order": {"type": "integer"},
        "task_count": {"type": "integer", "minimum": 0},
    },
}

TASK_SCHEMA = {
    "type": "object",
    "required": ["id", "title", "column", "order", "created_at", "updated_at"],
    "properties": {
        "id": {"type": "integer"},
        "title": {"type": "string", "minLength": 1},
        "description": {"type": "string"},
        "column": {"type": "integer"},
        "column_name": {"type": "string"},
        "order": {"type": "integer"},
        "created_at": {"type": "string"},
        "updated_at": {"type": "string"},
    },
}

BOARD_SCHEMA = {
    "type": "object",
    "required": ["columns"],
    "properties": {
        "columns": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "name", "order", "tasks"],
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "order": {"type": "integer"},
                    "tasks": {"type": "array"},
                },
            },
        },
    },
}

AUTH_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["user", "token"],
    "properties": {
        "user": {
            "type": "object",
            "required": ["id", "username"],
            "properties": {
                "id": {"type": "integer"},
                "username": {"type": "string"},
                "email": {"type": "string"},
            },
        },
        "token": {"type": "string", "minLength": 1},
    },
}


@pytest.mark.django_db
class TestColumnContractSchema:
    
    def test_column_list_schema(self, auth_client, user, clean_db):
        ColumnFactory.create_batch(2, user=user)
        response = auth_client.get('/api/v1/columns/')
        
        for column in response.data['results']:
            validate(instance=column, schema=COLUMN_SCHEMA)
    
    def test_column_create_schema(self, auth_client, user, clean_db):
        response = auth_client.post('/api/v1/columns/', {'name': 'Test'})
        validate(instance=response.data, schema=COLUMN_SCHEMA)


@pytest.mark.django_db
class TestTaskContractSchema:
    
    def test_task_list_schema(self, auth_client, user, clean_db):
        column = ColumnFactory(user=user)
        TaskFactory.create_batch(2, column=column, user=user)
        
        response = auth_client.get('/api/v1/tasks/')
        for task in response.data['results']:
            validate(instance=task, schema=TASK_SCHEMA)
    
    def test_task_create_schema(self, auth_client, user, clean_db):
        column = ColumnFactory(user=user)
        response = auth_client.post('/api/v1/tasks/', {
            'title': 'Test Task',
            'column_id': column.id
        })
        validate(instance=response.data, schema=TASK_SCHEMA)


@pytest.mark.django_db
class TestBoardContractSchema:
    
    def test_board_schema(self, auth_client, user, clean_db):
        col = ColumnFactory(user=user)
        TaskFactory.create_batch(2, column=col, user=user)
        
        response = auth_client.get('/api/v1/board/')
        validate(instance=response.data, schema=BOARD_SCHEMA)


@pytest.mark.django_db
class TestAuthContractSchema:
    
    def test_register_response_schema(self, api_client, clean_db):
        response = api_client.post('/api/v1/auth/register/', {
            'username': 'testuser',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
        })
        validate(instance=response.data, schema=AUTH_RESPONSE_SCHEMA)
    
    def test_login_response_schema(self, api_client, user, clean_db):
        response = api_client.post('/api/v1/auth/login/', {
            'username': user.username,
            'password': 'testpass123',
        })
        validate(instance=response.data, schema=AUTH_RESPONSE_SCHEMA)
