"""
app.schemas.intervention — Intervention API Request & Response Schemas
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from app.models.intervention import (
    InterventionOutcome,
    InterventionStatus,
    InterventionType,
)


class InterventionCreate(BaseModel):
    student_id: str = Field(..., min_length=1)
    school_id: str = Field(..., min_length=1)
    class_id: str = Field(..., min_length=1)
    type: InterventionType
    notes: str = Field(..., min_length=2, max_length=1000)
    follow_up_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class InterventionUpdate(BaseModel):
    type: Optional[InterventionType] = None
    notes: Optional[str] = Field(None, min_length=2, max_length=1000)
    follow_up_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    status: Optional[InterventionStatus] = None
    outcome: Optional[InterventionOutcome] = None
    outcome_notes: Optional[str] = Field(None, max_length=1000)


class InterventionResponse(BaseModel):
    id: str
    school_id: str
    student_id: str
    teacher_id: str
    class_id: str
    type: InterventionType
    notes: str
    follow_up_date: Optional[str]
    status: InterventionStatus
    outcome: Optional[InterventionOutcome]
    outcome_notes: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, intervention) -> "InterventionResponse":
        return cls(
            id=intervention.id,
            school_id=intervention.school_id,
            student_id=intervention.student_id,
            teacher_id=intervention.teacher_id,
            class_id=intervention.class_id,
            type=intervention.type,
            notes=intervention.notes,
            follow_up_date=intervention.follow_up_date,
            status=intervention.status,
            outcome=intervention.outcome,
            outcome_notes=intervention.outcome_notes,
            created_at=intervention.created_at.isoformat(),
            updated_at=intervention.updated_at.isoformat(),
        )
