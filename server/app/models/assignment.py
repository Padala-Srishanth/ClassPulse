"""
app.models.assignment — Assignment & AssignmentSubmission Domain Models

Assignment: A classwork task / homework assignment created by a teacher.
AssignmentSubmission: A student's submitted response, attachments, marks, and feedback.

Collections:
  assignments/{assignmentId}
  assignments/{assignmentId}/submissions/{submissionId}
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AssignmentStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"


class SubmissionStatus(str, Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    LATE = "LATE"
    GRADED = "GRADED"
    RESUBMISSION_REQUESTED = "RESUBMISSION_REQUESTED"


class AssignmentAttachment(BaseModel):
    title: str
    url: str
    file_type: str = "link"  # "pdf" | "link" | "document"


class Assignment(BaseModel):
    """A classwork or homework assignment created for a class."""

    id: str  # Firestore document ID (UUID)
    school_id: str
    class_id: str
    teacher_id: str
    teacher_name: str
    title: str
    subject: str
    description: str = ""
    due_date: str  # ISO format: YYYY-MM-DD
    due_time: str = "23:59"  # 24-hour format: HH:MM
    max_marks: float = 20.0
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    status: AssignmentStatus = AssignmentStatus.PUBLISHED
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "Assignment":
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


class AssignmentSubmission(BaseModel):
    """One student's submission and grading record for an assignment."""

    id: str  # Deterministic: hash(assignment_id + ":" + student_id)
    assignment_id: str
    school_id: str
    class_id: str
    student_id: str
    student_name: str
    student_code: str
    submitted_at: Optional[datetime] = None
    content: Optional[str] = None  # Student's written answer or notes
    attachment_name: Optional[str] = None
    attachment_url: Optional[str] = None
    status: SubmissionStatus = SubmissionStatus.PENDING
    is_late: bool = False
    obtained_marks: Optional[float] = None
    feedback: Optional[str] = None
    graded_by: Optional[str] = None
    graded_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @property
    def percentage(self) -> Optional[float]:
        if self.obtained_marks is None:
            return None
        return round(self.obtained_marks, 2)

    @staticmethod
    def make_id(assignment_id: str, student_id: str) -> str:
        raw = f"{assignment_id}:{student_id}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "AssignmentSubmission":
        data = dict(data)
        data["id"] = doc_id
        for ts_field in ("created_at", "updated_at", "submitted_at", "graded_at"):
            if ts_field in data and data[ts_field] and hasattr(data[ts_field], "timestamp"):
                from datetime import datetime as dt
                data[ts_field] = dt.fromtimestamp(data[ts_field].timestamp(), tz=timezone.utc)
        return cls(**data)

    def to_firestore(self) -> dict:
        d = self.model_dump(exclude={"id"})
        d["status"] = self.status.value
        return d
