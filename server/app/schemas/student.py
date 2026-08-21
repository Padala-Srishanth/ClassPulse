"""
app.schemas.student — Student API Request/Response Schemas
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from app.models.student import StudentStatus


class StudentCreate(BaseModel):
    school_id: str = Field(..., min_length=1)
    class_id: str = Field(..., min_length=1)
    student_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=150)
    grade: str = Field(..., min_length=1, max_length=20)
    section: str = Field(..., min_length=1, max_length=20)
    parent_contact: Optional[str] = Field(None, max_length=100)


class StudentUpdate(BaseModel):
    class_id: Optional[str] = None
    student_code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    grade: Optional[str] = Field(None, min_length=1, max_length=20)
    section: Optional[str] = Field(None, min_length=1, max_length=20)
    parent_contact: Optional[str] = Field(None, max_length=100)
    status: Optional[StudentStatus] = None


class StudentResponse(BaseModel):
    id: str
    school_id: str
    class_id: str
    student_code: str
    name: str
    grade: str
    section: str
    parent_contact: Optional[str] = None
    status: StudentStatus
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, student) -> "StudentResponse":
        return cls(
            id=student.id,
            school_id=student.school_id,
            class_id=student.class_id,
            student_code=student.student_code,
            name=student.name,
            grade=student.grade,
            section=student.section,
            parent_contact=getattr(student, "parent_contact", None),
            status=student.status,
            created_at=student.created_at.isoformat(),
            updated_at=student.updated_at.isoformat(),
        )

