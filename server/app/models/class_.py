"""
app.models.class_ — Class Domain Model

Represents a classroom within a school.
teacher_ids is a list of Firebase UIDs of assigned teachers.
File named class_.py to avoid shadowing the Python builtin 'class'.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ClassStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Class(BaseModel):
    """Internal domain model for a school class/section."""

    id: str
    school_id: str
    name: str                        # e.g. "Class 10 - A"
    grade: str                       # e.g. "10"
    section: str                     # e.g. "A"
    academic_year: str               # e.g. "2024-25"
    teacher_ids: List[str] = Field(default_factory=list)
    status: ClassStatus = ClassStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "Class":
        data = dict(data)
        data["id"] = doc_id
        for ts_field in ("created_at", "updated_at"):
            if ts_field in data and hasattr(data[ts_field], "timestamp"):
                from datetime import datetime as dt
                data[ts_field] = dt.fromtimestamp(
                    data[ts_field].timestamp(), tz=timezone.utc
                )
        return cls(**data)

    def to_firestore(self) -> dict:
        d = self.model_dump(exclude={"id"})
        d["status"] = self.status.value
        return d
