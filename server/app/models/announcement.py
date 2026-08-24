"""
app.models.announcement — Announcement Domain Model

Announcements can target: all_school, teachers, students, specific class/section.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AnnouncementTarget(str, Enum):
    ALL_SCHOOL = "ALL_SCHOOL"
    TEACHERS = "TEACHERS"
    STUDENTS = "STUDENTS"
    CLASS = "CLASS"
    SECTION = "SECTION"


class Announcement(BaseModel):
    """A school announcement with targeting."""

    id: str
    school_id: str
    created_by: str            # UID of creator
    created_by_name: str       # Display name
    title: str
    message: str
    target: AnnouncementTarget
    target_class_id: Optional[str] = None   # Only for CLASS / SECTION targets
    expires_at: Optional[str] = None        # ISO date YYYY-MM-DD
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "Announcement":
        data = dict(data)
        data["id"] = doc_id
        for ts_field in ("created_at", "updated_at"):
            if ts_field in data and hasattr(data[ts_field], "timestamp"):
                from datetime import datetime as dt
                data[ts_field] = dt.fromtimestamp(data[ts_field].timestamp(), tz=timezone.utc)
        return cls(**data)

    def to_firestore(self) -> dict:
        d = self.model_dump(exclude={"id"})
        d["target"] = self.target.value
        return d
