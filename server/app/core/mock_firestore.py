"""
app.core.mock_firestore — In-Memory Firestore Engine & Demo Data Seeder
Provides local in-memory Firestore storage when Cloud Firestore API is disabled or running offline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional
import uuid


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

        if self._order_field:
            filtered.sort(key=lambda x: str(x[1].get(self._order_field, "")))

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


# Global Singleton for local in-memory Firestore
_local_db_instance = MockFirestore()


def get_local_firestore() -> MockFirestore:
    return _local_db_instance


def seed_local_demo_data(db: MockFirestore):
    """Seed comprehensive 14-class, 35-teacher, 630-student demo dataset in memory."""
    try:
        from seed_demo_data import seed_demo_data
        seed_demo_data(school_id="school-001", reset_existing=False)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Error in seed_local_demo_data: %s", exc)

