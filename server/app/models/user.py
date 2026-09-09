"""
app.models.user — User Domain Model

Application-level user profile stored in Firestore.
Authentication identity remains in Firebase Auth.
The document ID is the Firebase UID.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.core.security import UserRole


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class User(BaseModel):
    """Internal domain model for an application user."""

    id: str                    # Firebase UID — same as Firestore document ID
    firebase_uid: str
    email: str
    name: str
    role: UserRole
    school_id: Optional[str] = None   # None only for ADMIN
    status: UserStatus = UserStatus.ACTIVE
    subjects: list[str] = Field(default_factory=list)
    assigned_classes: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "User":
        data = dict(data)
        data["id"] = doc_id
        if "subjects" not in data or data["subjects"] is None:
            data["subjects"] = []
        if "assigned_classes" not in data or data["assigned_classes"] is None:
            data["assigned_classes"] = []
        for ts_field in ("created_at", "updated_at"):
            if ts_field in data and hasattr(data[ts_field], "timestamp"):
                from datetime import datetime as dt
                data[ts_field] = dt.fromtimestamp(
                    data[ts_field].timestamp(), tz=timezone.utc
                )
        return cls(**data)

    def to_firestore(self) -> dict:
        d = self.model_dump(exclude={"id"})
        d["role"] = self.role.value
        d["status"] = self.status.value
        d["subjects"] = self.subjects
        d["assigned_classes"] = self.assigned_classes
        return d
