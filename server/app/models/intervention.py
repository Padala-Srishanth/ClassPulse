"""
app.models.intervention — Intervention Domain Model
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class InterventionType(str, Enum):
    ACADEMIC_SUPPORT = "ACADEMIC_SUPPORT"
    PARENT_CONTACT = "PARENT_CONTACT"
    COUNSELING_REFERRAL = "COUNSELING_REFERRAL"
    EXTRA_ASSIGNMENT = "EXTRA_ASSIGNMENT"
    ONE_ON_ONE_SUPPORT = "ONE_ON_ONE_SUPPORT"
    OTHER = "OTHER"


class InterventionStatus(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class InterventionOutcome(str, Enum):
    STUDENT_IMPROVED = "STUDENT_IMPROVED"
    STUDENT_UNCHANGED = "STUDENT_UNCHANGED"
    STUDENT_DECLINED_FURTHER = "STUDENT_DECLINED_FURTHER"
    REFERRED_FOR_ADDITIONAL_SUPPORT = "REFERRED_FOR_ADDITIONAL_SUPPORT"
    OTHER = "OTHER"


class Intervention(BaseModel):
    """Domain model for teacher interventions tracked in Firestore."""

    id: str
    school_id: str
    student_id: str
    teacher_id: str
    class_id: str
    type: InterventionType
    notes: str
    follow_up_date: Optional[str] = None  # YYYY-MM-DD
    status: InterventionStatus = InterventionStatus.PLANNED
    outcome: Optional[InterventionOutcome] = None
    outcome_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "Intervention":
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
        d["type"] = self.type.value
        d["status"] = self.status.value
        if self.outcome:
            d["outcome"] = self.outcome.value
        return d
