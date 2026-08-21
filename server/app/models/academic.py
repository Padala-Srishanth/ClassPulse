"""
app.models.academic — Academic Record Domain Models

Contains internal domain models for:
  - AttendanceRecord
  - HomeworkRecord
  - TestScoreRecord

These are stored as subcollections under students/{studentId}/.
The document ID is deterministic (hash of natural key) to ensure idempotency.

Deduplication keys:
  Attendance:  sha256(student_id + ":" + date)
  Homework:    sha256(student_id + ":" + assignment_id + ":" + assignment_date)
  TestScore:   sha256(student_id + ":" + subject + ":" + assessment_name + ":" + assessment_date)
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------

class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"


class AttendanceRecord(BaseModel):
    """One day's attendance for one student."""

    id: str                         # Deterministic doc ID
    student_id: str
    school_id: str
    class_id: str
    date: str                        # ISO format: YYYY-MM-DD
    status: AttendanceStatus
    source: str = "csv"              # "csv" | "manual"
    import_batch_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @staticmethod
    def make_id(student_id: str, date_str: str) -> str:
        """Deterministic document ID from student_id + date."""
        raw = f"{student_id}:{date_str}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "AttendanceRecord":
        data = dict(data)
        data["id"] = doc_id
        if "created_at" in data and hasattr(data["created_at"], "timestamp"):
            from datetime import datetime as dt
            data["created_at"] = dt.fromtimestamp(
                data["created_at"].timestamp(), tz=timezone.utc
            )
        return cls(**data)

    def to_firestore(self) -> dict:
        d = self.model_dump(exclude={"id"})
        d["status"] = self.status.value
        return d


# ---------------------------------------------------------------------------
# Homework
# ---------------------------------------------------------------------------

class HomeworkStatus(str, Enum):
    COMPLETED = "COMPLETED"
    NOT_COMPLETED = "NOT_COMPLETED"
    LATE = "LATE"


class HomeworkRecord(BaseModel):
    """One homework assignment completion record for one student."""

    id: str
    student_id: str
    school_id: str
    class_id: str
    assignment_id: str               # School's assignment identifier
    assignment_date: str             # ISO format: YYYY-MM-DD
    status: HomeworkStatus
    source: str = "csv"
    import_batch_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @staticmethod
    def make_id(student_id: str, assignment_id: str, assignment_date: str) -> str:
        raw = f"{student_id}:{assignment_id}:{assignment_date}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "HomeworkRecord":
        data = dict(data)
        data["id"] = doc_id
        if "created_at" in data and hasattr(data["created_at"], "timestamp"):
            from datetime import datetime as dt
            data["created_at"] = dt.fromtimestamp(
                data["created_at"].timestamp(), tz=timezone.utc
            )
        return cls(**data)

    def to_firestore(self) -> dict:
        d = self.model_dump(exclude={"id"})
        d["status"] = self.status.value
        return d


# ---------------------------------------------------------------------------
# Test Score
# ---------------------------------------------------------------------------

class TestScoreRecord(BaseModel):
    """One test/assessment score for one student."""

    __test__ = False

    id: str

    student_id: str
    school_id: str
    class_id: str
    subject: str
    assessment_name: str
    assessment_date: str             # ISO format: YYYY-MM-DD
    score: float                     # Raw score achieved
    max_score: float                 # Maximum possible score
    source: str = "csv"
    import_batch_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @property
    def percentage(self) -> float:
        """Score as a percentage (0–100). Used by Phase 3 ML."""
        if self.max_score <= 0:
            return 0.0
        return round((self.score / self.max_score) * 100, 2)

    @staticmethod
    def make_id(
        student_id: str, subject: str, assessment_name: str, assessment_date: str
    ) -> str:
        raw = f"{student_id}:{subject}:{assessment_name}:{assessment_date}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "TestScoreRecord":
        data = dict(data)
        data["id"] = doc_id
        if "created_at" in data and hasattr(data["created_at"], "timestamp"):
            from datetime import datetime as dt
            data["created_at"] = dt.fromtimestamp(
                data["created_at"].timestamp(), tz=timezone.utc
            )
        return cls(**data)

    def to_firestore(self) -> dict:
        return self.model_dump(exclude={"id"})
