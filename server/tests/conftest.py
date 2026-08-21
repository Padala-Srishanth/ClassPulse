"""
tests/conftest.py — Shared Test Fixtures

Provides reusable pytest fixtures for all ClassPulse tests.

Key design decisions:
  - Firebase is MOCKED in tests. Real Firebase credentials are not required
    to run the test suite. This makes CI/CD safe and credential-free.
  - Settings are overridden via environment variables before the app is
    imported, ensuring consistent test configuration.
  - The TestClient uses FastAPI's ASGI transport — no real HTTP server needed.

How Firebase mocking works:
  - firebase_admin.initialize_app and auth.verify_id_token are patched.
  - Tests that need a specific user identity pass a mock decoded token.
  - This allows testing auth logic without real Firebase tokens.

Usage:
    def test_something(client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_auth_route(auth_client):
        response = auth_client.get("/api/v1/some-protected-route")
        ...
"""

import os
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Set test environment variables BEFORE importing app modules.
# This ensures get_settings() returns test-safe values.
# ---------------------------------------------------------------------------
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("APP_NAME", "ClassPulse API Test")
os.environ.setdefault("APP_VERSION", "test")
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project-id")
os.environ.setdefault("FIREBASE_CLIENT_EMAIL", "test@test-project-id.iam.gserviceaccount.com")
os.environ.setdefault("FIREBASE_PRIVATE_KEY", "-----BEGIN RSA PRIVATE KEY-----\nMOCK_KEY\n-----END RSA PRIVATE KEY-----")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("HIDE_ERROR_DETAILS", "false")


# ---------------------------------------------------------------------------
# Mock Firebase at the module level before app.core.firebase is imported.
# ---------------------------------------------------------------------------

# We patch firebase_admin.initialize_app and firebase_admin.credentials.Certificate
# so that no real Firebase connection is attempted during tests.
_mock_firebase_app = MagicMock()
_mock_firestore_client = MagicMock()

# Mock the collections() call used by check_firebase_connectivity
_mock_firestore_client.collections.return_value = iter([])


@pytest.fixture(scope="session", autouse=True)
def mock_firebase_admin():
    """
    Session-scoped fixture that patches Firebase Admin SDK for all tests.

    Patches:
      - firebase_admin.initialize_app → returns a mock App
      - firebase_admin.get_app        → raises ValueError (simulates first init)
      - firebase_admin.credentials.Certificate → accepts any dict
      - firestore.client              → returns our mock Firestore client
    """
    with (
        patch("firebase_admin.initialize_app", return_value=_mock_firebase_app),
        patch("firebase_admin.credentials.Certificate", return_value=MagicMock()),
        patch("firebase_admin.firestore.client", return_value=_mock_firestore_client),
        patch("firebase_admin.storage.bucket", return_value=MagicMock()),
        # Simulate no existing app (first init path)
        patch("firebase_admin.get_app", side_effect=ValueError("No app")),
    ):
        yield


# ---------------------------------------------------------------------------
# Clear the settings LRU cache between tests so env var changes take effect
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def clear_settings_cache():
    from app.core.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Clear the Firebase singleton between tests so each test gets fresh state
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def reset_firebase_singleton():
    """Reset the Firebase module-level singletons before each test."""
    import app.core.firebase as fb
    original_app = fb._firebase_app
    original_client = fb._firestore_client
    fb._firebase_app = None
    fb._firestore_client = None
    yield
    fb._firebase_app = original_app
    fb._firestore_client = original_client


# ---------------------------------------------------------------------------
# Test client fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    """Return a fresh FastAPI application instance for testing."""
    from app.main import create_application
    return create_application()


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    """
    Unauthenticated test client.

    Use for testing public endpoints like /health.
    """
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def mock_teacher_token() -> dict:
    """
    A mock decoded Firebase token representing a TEACHER user.

    Use this to simulate authenticated requests from a teacher.
    """
    return {
        "uid": "teacher-uid-001",
        "email": "teacher@school.example.com",
        "email_verified": True,
        "role": "TEACHER",
        "school_id": "school-001",
        "sub": "teacher-uid-001",
    }


@pytest.fixture
def mock_admin_token() -> dict:
    """
    A mock decoded Firebase token representing a platform ADMIN user.
    """
    return {
        "uid": "admin-uid-001",
        "email": "admin@classpulse.example.com",
        "email_verified": True,
        "role": "ADMIN",
        "school_id": None,
        "sub": "admin-uid-001",
    }
