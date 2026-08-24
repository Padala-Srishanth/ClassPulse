"""
app.models.meeting — MeetingRequest Domain Model

Used for:
  - Student requesting meeting with teacher
  - Student requesting appointment with principal
  - Teacher inviting student for a meeting
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MeetingType(str, Enum):
    STUDENT_TEACHER = "STUDENT_TEACHER"
    STUDENT_PRINCIPAL = "STUDENT_PRINCIPAL"
    TEACHER_STUDENT = "TEACHER_STUDENT"      # Teacher invites student


class MeetingStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class MeetingRequest(BaseModel):
    """A meeting request between two parties in the school."""

    id: str
    school_id: str
    meeting_type: MeetingType
    requested_by: str          # UID of requester
    requested_by_name: str
    requested_to: str          # UID of target
    requested_to_name: str
    subject: str
    message: str
    proposed_date: str         # ISO format: YYYY-MM-DD
    proposed_time: Optional[str] = None  # HH:MM
    status: MeetingStatus = MeetingStatus.PENDING
    response_note: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "MeetingRequest":
        data = dict(data)
        data["id"] = doc_id
        for ts_field in ("created_at", "updated_at"):
            if ts_field in data and hasattr(data[ts_field], "timestamp"):
                from datetime import datetime as dt
                data[ts_field] = dt.fromtimestamp(data[ts_field].timestamp(), tz=timezone.utc)
        return cls(**data)

    def to_firestore(self) -> dict:
        d = self.model_dump(exclude={"id"})
        d["meeting_type"] = self.meeting_type.value
        d["status"] = self.status.value
        return d
