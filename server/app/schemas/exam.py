"""
app.schemas.exam — Exam API Request/Response Schemas
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.exam import ExamStatus


class ExamCreate(BaseModel):
    __test__ = False

    school_id: str = Field(..., min_length=1)
    class_id: str = Field(..., min_length=1)
    exam_name: str = Field(..., min_length=1, max_length=200)
    subject: str = Field(..., min_length=1, max_length=100)
    exam_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    max_marks: float = Field(..., gt=0.0)


class ExamResponse(BaseModel):
    __test__ = False

    id: str
    school_id: str
    class_id: str
    teacher_id: str
    exam_name: str
    subject: str
    exam_date: str
    max_marks: float
    status: str
    created_at: str

    @classmethod
    def from_model(cls, exam) -> "ExamResponse":
        return cls(
            id=exam.id,
            school_id=exam.school_id,
            class_id=exam.class_id,
            teacher_id=exam.teacher_id,
            exam_name=exam.exam_name,
            subject=exam.subject,
            exam_date=exam.exam_date,
            max_marks=exam.max_marks,
            status=exam.status.value,
            created_at=exam.created_at.isoformat(),
        )


class ExamResultCreate(BaseModel):
    __test__ = False
    student_id: str = Field(..., min_length=1)
    obtained_marks: float = Field(..., ge=0.0)


class BulkExamResultCreate(BaseModel):
    __test__ = False
    results: List[ExamResultCreate] = Field(..., min_length=1)


class ExamResultResponse(BaseModel):
    __test__ = False

    id: str
    exam_id: str
    school_id: str
    class_id: str
    student_id: str
    obtained_marks: float
    max_marks: float
    percentage: float
    grade: str
    created_at: str

    @classmethod
    def from_model(cls, result) -> "ExamResultResponse":
        return cls(
            id=result.id,
            exam_id=result.exam_id,
            school_id=result.school_id,
            class_id=result.class_id,
            student_id=result.student_id,
            obtained_marks=result.obtained_marks,
            max_marks=result.max_marks,
            percentage=result.percentage,
            grade=result.grade,
            created_at=result.created_at.isoformat(),
        )
