"""
app.models.exam — Exam and ExamResult Domain Models

Exam: A test/assessment created by a teacher for a class.
ExamResult: One student's marks in one exam.

Collections:
  exams/{examId}
  exams/{examId}/results/{resultId}

Percentage is always computed: (obtained / maximum) * 100, never stored as raw %.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ExamStatus(str, Enum):
    UPCOMING = "UPCOMING"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Exam(BaseModel):
    """A scheduled exam/test for a class."""

    id: str                    # Firestore document ID
    school_id: str
    class_id: str
    teacher_id: str
    exam_name: str
    subject: str
    exam_date: str             # ISO format: YYYY-MM-DD
    max_marks: float           # Maximum possible marks
    status: ExamStatus = ExamStatus.UPCOMING
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "Exam":
        data = dict(data)
        data["id"] = doc_id
        for ts_field in ("created_at", "updated_at"):
            if ts_field in data and hasattr(data[ts_field], "timestamp"):
                from datetime import datetime as dt
                data[ts_field] = dt.fromtimestamp(data[ts_field].timestamp(), tz=timezone.utc)
        return cls(**data)

    def to_firestore(self) -> dict:
        d = self.model_dump(exclude={"id"})
        d["status"] = self.status.value
        return d


class ExamResult(BaseModel):
    """One student's result in one exam."""

    __test__ = False

    id: str                    # Deterministic: hash(exam_id + student_id)
    exam_id: str
    school_id: str
    class_id: str
    student_id: str
    obtained_marks: float      # Marks scored (0 to max_marks)
    max_marks: float           # Copy of exam max_marks for self-contained calculations
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @property
    def percentage(self) -> float:
        """Always returns obtained / max * 100. Never multiplied twice."""
        if self.max_marks <= 0:
            return 0.0
        return round((self.obtained_marks / self.max_marks) * 100, 2)

    @property
    def grade(self) -> str:
        """Letter grade based on percentage."""
        pct = self.percentage
        if pct >= 90:
            return "A+"
        if pct >= 80:
            return "A"
        if pct >= 70:
            return "B"
        if pct >= 60:
            return "C"
        if pct >= 50:
            return "D"
        return "F"

    @staticmethod
    def make_id(exam_id: str, student_id: str) -> str:
        raw = f"{exam_id}:{student_id}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "ExamResult":
        data = dict(data)
        data["id"] = doc_id
        for ts_field in ("created_at", "updated_at"):
            if ts_field in data and hasattr(data[ts_field], "timestamp"):
                from datetime import datetime as dt
                data[ts_field] = dt.fromtimestamp(data[ts_field].timestamp(), tz=timezone.utc)
        return cls(**data)

    def to_firestore(self) -> dict:
        return self.model_dump(exclude={"id"})
