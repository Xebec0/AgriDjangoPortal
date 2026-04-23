import os

import pytest
from django.contrib.auth.models import User
from django.test import Client


@pytest.fixture(autouse=True)
def _media_root(tmp_path, settings):
    """
    Isolate file uploads per-test run.

    Many app features validate and store uploaded files; using a temp MEDIA_ROOT keeps
    tests hermetic and avoids touching real user/dev files.
    """
    settings.MEDIA_ROOT = tmp_path / "media"
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)


@pytest.fixture(autouse=True)
def _clear_request_context():
    """
    Ensure thread-local request context never leaks across tests.

    The app's audit signals use `core.middleware` thread locals to attribute ActivityLog
    entries to a user/ip; in tests we want deterministic behavior and no cross-test FK issues.
    """
    from core.middleware import set_request_context

    set_request_context(None, None, None)
    yield
    set_request_context(None, None, None)


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="user", password="TestPass123!")


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username="staff",
        password="TestPass123!",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def authed_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(client, staff_user):
    client.force_login(staff_user)
    return client

