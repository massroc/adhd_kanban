"""Pytest configuration and shared fixtures."""

import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create and return a test user."""
    from kanban.tests.factories import UserFactory
    return UserFactory()


@pytest.fixture
def auth_client(api_client, user):
    """Return an authenticated API client."""
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client
