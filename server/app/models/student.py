"""
app.models.student — Student Domain Model

Represents a student within a school and class.
PII is minimised — date_of_birth is deliberately omitted from MVP.
student_code is the school's own identifier (used for CSV matching).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class StudentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    TRANSFERRED = "TRANSFERRED"


class Student(BaseModel):
    """Internal domain model for a student."""

    id: str                        # Firestore auto-generated document ID
    school_id: str
    class_id: str
    student_code: str              # School's own student identifier (for CSV matching)
    name: str
    grade: str
    section: str
    status: StudentStatus = StudentStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    # Note: date_of_birth intentionally omitted in MVP to minimise PII.
    # Add if Phase 3 requires age-group analysis.

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "Student":
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
