"""
tests/conftest.py — Shared Test Fixtures & In-Memory Firestore Mock
"""

import os
from typing import Any, Dict, Generator, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Set test environment variables BEFORE importing app modules.
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
# In-Memory Firestore Mock Implementation
# ---------------------------------------------------------------------------

class MockDocumentSnapshot:
    def __init__(self, doc_id: str, data: Optional[Dict[str, Any]]):
        self.id = doc_id
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data) if self._data is not None else {}


class MockDocumentReference:
    def __init__(self, doc_id: str, store: Dict[str, Any], subcollections: Dict[str, Any]):
        self.id = doc_id
        self._store = store
        self._subcollections = subcollections

    def get(self) -> MockDocumentSnapshot:
        return MockDocumentSnapshot(self.id, self._store.get(self.id))

    def set(self, data: Dict[str, Any]):
        self._store[self.id] = dict(data)

    def update(self, data: Dict[str, Any]):
        if self.id in self._store:
            self._store[self.id].update(data)
        else:
            self._store[self.id] = dict(data)

    def collection(self, name: str) -> "MockCollectionReference":
        key = f"{self.id}/{name}"
        if key not in self._subcollections:
            self._subcollections[key] = {}
        return MockCollectionReference(self._subcollections[key], self._subcollections)


class MockQuery:
    def __init__(self, store: Dict[str, Any], subcollections: Dict[str, Any], filters=None, order_field=None, offset_val=0, limit_val=None):
        self._store = store
        self._subcollections = subcollections
        self._filters = filters or []
        self._order_field = order_field
        self._offset_val = offset_val
        self._limit_val = limit_val

    def where(self, field: str, op: str, value: Any) -> "MockQuery":
        new_filters = list(self._filters)
        new_filters.append((field, op, value))
        return MockQuery(self._store, self._subcollections, new_filters, self._order_field, self._offset_val, self._limit_val)

    def order_by(self, field: str) -> "MockQuery":
        return MockQuery(self._store, self._subcollections, self._filters, field, self._offset_val, self._limit_val)

    def offset(self, val: int) -> "MockQuery":
        return MockQuery(self._store, self._subcollections, self._filters, self._order_field, val, self._limit_val)

    def limit(self, val: int) -> "MockQuery":
        return MockQuery(self._store, self._subcollections, self._filters, self._order_field, self._offset_val, val)

    def stream(self) -> Generator[MockDocumentSnapshot, None, None]:
        items = list(self._store.items())
        
        # Apply filters
        filtered = []
        for doc_id, doc_data in items:
            match = True
            for field, op, val in self._filters:
                if op == "==":
                    if doc_data.get(field) != val:
                        match = False
                        break
            if match:
                filtered.append((doc_id, doc_data))

        # Apply ordering if any
        if self._order_field:
            filtered.sort(key=lambda x: str(x[1].get(self._order_field, "")))

        # Apply offset and limit
        if self._offset_val:
            filtered = filtered[self._offset_val:]
        if self._limit_val is not None:
            filtered = filtered[:self._limit_val]

        for doc_id, doc_data in filtered:
            yield MockDocumentSnapshot(doc_id, doc_data)


class MockCollectionReference(MockQuery):
    def __init__(self, store: Dict[str, Any], subcollections: Dict[str, Any]):
        super().__init__(store, subcollections)

    def document(self, doc_id: str) -> MockDocumentReference:
        return MockDocumentReference(doc_id, self._store, self._subcollections)


class MockBatch:
    def __init__(self, root_db: "MockFirestore"):
        self._ops = []
        self._root_db = root_db

    def set(self, doc_ref: MockDocumentReference, data: Dict[str, Any]):
        self._ops.append(("set", doc_ref, data))

    def commit(self):
        for op, doc_ref, data in self._ops:
            if op == "set":
                doc_ref.set(data)
        self._ops.clear()


class MockFirestore:
    def __init__(self):
        self._collections: Dict[str, Dict[str, Any]] = {}
        self._subcollections: Dict[str, Dict[str, Any]] = {}

    def collection(self, name: str) -> MockCollectionReference:
        if name not in self._collections:
            self._collections[name] = {}
        return MockCollectionReference(self._collections[name], self._subcollections)

    def collections(self):
        return iter([self.collection(k) for k in self._collections])

    def batch(self) -> MockBatch:
        return MockBatch(self)

    def clear(self):
        self._collections.clear()
        self._subcollections.clear()


# Shared singleton mock firestore instance
mock_db = MockFirestore()


# ---------------------------------------------------------------------------
# Global Pytest Mocking
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def mock_firebase_admin():
    _mock_app = MagicMock()
    with (
        patch("firebase_admin.initialize_app", return_value=_mock_app),
        patch("firebase_admin.credentials.Certificate", return_value=MagicMock()),
        patch("firebase_admin.firestore.client", return_value=mock_db),
        patch("firebase_admin.storage.bucket", return_value=MagicMock()),
        patch("firebase_admin.get_app", side_effect=ValueError("No app")),
    ):
        yield


@pytest.fixture(autouse=True)
def clear_settings_cache():
    from app.core.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def reset_mock_db_and_singletons():
    mock_db.clear()
    import app.core.firebase as fb
    fb._firebase_app = MagicMock()
    fb._firestore_client = mock_db
    yield
    mock_db.clear()


# ---------------------------------------------------------------------------
# Client & Auth Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    from app.main import create_application
    return create_application()


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def mock_admin_token() -> dict:
    return {
        "uid": "admin-uid-001",
        "email": "admin@classpulse.example.com",
        "email_verified": True,
        "role": "ADMIN",
        "school_id": None,
        "sub": "admin-uid-001",
    }


@pytest.fixture
def mock_school_admin_token() -> dict:
    return {
        "uid": "sadmin-uid-001",
        "email": "admin@school-001.example.com",
        "email_verified": True,
        "role": "SCHOOL_ADMIN",
        "school_id": "school-001",
        "sub": "sadmin-uid-001",
    }


@pytest.fixture
def mock_teacher_token() -> dict:
    return {
        "uid": "teacher-uid-001",
        "email": "teacher@school-001.example.com",
        "email_verified": True,
        "role": "TEACHER",
        "school_id": "school-001",
        "sub": "teacher-uid-001",
    }


@pytest.fixture
def mock_other_teacher_token() -> dict:
    return {
        "uid": "teacher-uid-002",
        "email": "teacher@school-002.example.com",
        "email_verified": True,
        "role": "TEACHER",
        "school_id": "school-002",
        "sub": "teacher-uid-002",
    }


def auth_client_factory(app, token_data):
    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=token_data)):
        c = TestClient(app, headers={"Authorization": "Bearer mock-token"}, raise_server_exceptions=False)
        yield c


@pytest.fixture
def admin_client(app, mock_admin_token):
    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_admin_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock-token"}, raise_server_exceptions=False) as c:
            yield c


@pytest.fixture
def school_admin_client(app, mock_school_admin_token):
    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_school_admin_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock-token"}, raise_server_exceptions=False) as c:
            yield c


@pytest.fixture
def teacher_client(app, mock_teacher_token):
    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_teacher_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock-token"}, raise_server_exceptions=False) as c:
            yield c


@pytest.fixture
def other_teacher_client(app, mock_other_teacher_token):
    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_other_teacher_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock-token"}, raise_server_exceptions=False) as c:
            yield c
