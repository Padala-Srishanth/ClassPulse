"""
app.schemas.class_ — Class API Request/Response Schemas
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.class_ import ClassStatus


class ClassCreate(BaseModel):
    school_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=100)
    grade: str = Field(..., min_length=1, max_length=20)
    section: str = Field(..., min_length=1, max_length=20)
    academic_year: str = Field(..., min_length=4, max_length=20)
    teacher_ids: List[str] = Field(default_factory=list)


class ClassUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    grade: Optional[str] = Field(None, min_length=1, max_length=20)
    section: Optional[str] = Field(None, min_length=1, max_length=20)
    academic_year: Optional[str] = Field(None, min_length=4, max_length=20)
    teacher_ids: Optional[List[str]] = None
    status: Optional[ClassStatus] = None


class ClassResponse(BaseModel):
    id: str
    school_id: str
    name: str
    grade: str
    section: str
    academic_year: str
    teacher_ids: List[str]
    status: ClassStatus
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, class_obj) -> "ClassResponse":
        return cls(
            id=class_obj.id,
            school_id=class_obj.school_id,
            name=class_obj.name,
            grade=class_obj.grade,
            section=class_obj.section,
            academic_year=class_obj.academic_year,
            teacher_ids=class_obj.teacher_ids,
            status=class_obj.status,
            created_at=class_obj.created_at.isoformat(),
            updated_at=class_obj.updated_at.isoformat(),
        )
