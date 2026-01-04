"""
Contract tests for the Kanban API.

These tests verify API responses match expected schemas.
"""

import pytest
from rest_framework.test import APIClient
from jsonschema import validate
from kanban.models import Column
from kanban.tests.factories import ColumnFactory, TaskFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def clean_db(db):
    Column.objects.all().delete()


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


@pytest.mark.django_db
class TestColumnContractSchema:
    
    def test_column_list_schema(self, api_client, clean_db):
        ColumnFactory.create_batch(2)
        response = api_client.get('/api/v1/columns/')
        
        for column in response.data['results']:
            validate(instance=column, schema=COLUMN_SCHEMA)
    
    def test_column_create_schema(self, api_client, clean_db):
        response = api_client.post('/api/v1/columns/', {'name': 'Test'})
        validate(instance=response.data, schema=COLUMN_SCHEMA)


@pytest.mark.django_db
class TestTaskContractSchema:
    
    def test_task_list_schema(self, api_client, clean_db):
        column = ColumnFactory()
        TaskFactory.create_batch(2, column=column)
        
        response = api_client.get('/api/v1/tasks/')
        for task in response.data['results']:
            validate(instance=task, schema=TASK_SCHEMA)
    
    def test_task_create_schema(self, api_client, clean_db):
        column = ColumnFactory()
        response = api_client.post('/api/v1/tasks/', {
            'title': 'Test Task',
            'column_id': column.id
        })
        validate(instance=response.data, schema=TASK_SCHEMA)


@pytest.mark.django_db
class TestBoardContractSchema:
    
    def test_board_schema(self, api_client, clean_db):
        col = ColumnFactory()
        TaskFactory.create_batch(2, column=col)
        
        response = api_client.get('/api/v1/board/')
        validate(instance=response.data, schema=BOARD_SCHEMA)
