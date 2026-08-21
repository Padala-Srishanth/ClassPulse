"""
app.schemas.academic — Academic API Request/Response Schemas
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from app.models.academic import AttendanceStatus, HomeworkStatus


# ---------------------------------------------------------------------------
# Attendance Schemas
# ---------------------------------------------------------------------------

class AttendanceCreate(BaseModel):
    student_id: str = Field(..., min_length=1)
    school_id: str = Field(..., min_length=1)
    class_id: str = Field(..., min_length=1)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    status: AttendanceStatus
    source: str = "manual"


class AttendanceResponse(BaseModel):
    id: str
    student_id: str
    school_id: str
    class_id: str
    date: str
    status: AttendanceStatus
    source: str
    created_at: str

    @classmethod
    def from_model(cls, record) -> "AttendanceResponse":
        return cls(
            id=record.id,
            student_id=record.student_id,
            school_id=record.school_id,
            class_id=record.class_id,
            date=record.date,
            status=record.status,
            source=record.source,
            created_at=record.created_at.isoformat(),
        )


# ---------------------------------------------------------------------------
# Homework Schemas
# ---------------------------------------------------------------------------

class HomeworkCreate(BaseModel):
    student_id: str = Field(..., min_length=1)
    school_id: str = Field(..., min_length=1)
    class_id: str = Field(..., min_length=1)
    assignment_id: str = Field(..., min_length=1)
    assignment_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    status: HomeworkStatus
    source: str = "manual"


class HomeworkResponse(BaseModel):
    id: str
    student_id: str
    school_id: str
    class_id: str
    assignment_id: str
    assignment_date: str
    status: HomeworkStatus
    source: str
    created_at: str

    @classmethod
    def from_model(cls, record) -> "HomeworkResponse":
        return cls(
            id=record.id,
            student_id=record.student_id,
            school_id=record.school_id,
            class_id=record.class_id,
            assignment_id=record.assignment_id,
            assignment_date=record.assignment_date,
            status=record.status,
            source=record.source,
            created_at=record.created_at.isoformat(),
        )


# ---------------------------------------------------------------------------
# Test Score Schemas
# ---------------------------------------------------------------------------

class TestScoreCreate(BaseModel):
    student_id: str = Field(..., min_length=1)
    school_id: str = Field(..., min_length=1)
    class_id: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1)
    assessment_name: str = Field(..., min_length=1)
    assessment_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    score: float = Field(..., ge=0.0)
    max_score: float = Field(..., gt=0.0)
    source: str = "manual"


class TestScoreResponse(BaseModel):
    id: str
    student_id: str
    school_id: str
    class_id: str
    subject: str
    assessment_name: str
    assessment_date: str
    score: float
    max_score: float
    percentage: float
    source: str
    created_at: str

    @classmethod
    def from_model(cls, record) -> "TestScoreResponse":
        return cls(
            id=record.id,
            student_id=record.student_id,
            school_id=record.school_id,
            class_id=record.class_id,
            subject=record.subject,
            assessment_name=record.assessment_name,
            assessment_date=record.assessment_date,
            score=record.score,
            max_score=record.max_score,
            percentage=record.percentage,
            source=record.source,
            created_at=record.created_at.isoformat(),
        )
