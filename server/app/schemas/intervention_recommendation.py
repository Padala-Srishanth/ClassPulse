"""
app.schemas.intervention_recommendation — API Schemas for Recommendations
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.intervention import InterventionType
from app.models.intervention_recommendation import (
    DismissalReason,
    InterventionRecommendation,
    PriorityLevel,
    RecommendationStatus,
)


class RecommendationApproveRequest(BaseModel):
    """Payload when teacher/principal approves a recommendation to create an intervention."""

    type: Optional[InterventionType] = None
    notes: Optional[str] = None
    follow_up_date: Optional[str] = None  # YYYY-MM-DD


class RecommendationDismissRequest(BaseModel):
    """Payload when teacher/principal dismisses a recommendation."""

    reason: str = DismissalReason.TEACHER_JUDGMENT.value
    notes: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Response envelope item for an intervention recommendation."""

    recommendation_id: str
    school_id: str
    student_id: str
    student_name: Optional[str] = None
    class_id: str
    class_name: Optional[str] = None
    risk_alert_id: Optional[str] = None
    report_period: str
    recommendation_type: InterventionType
    priority_level: PriorityLevel
    priority_score: float
    status: RecommendationStatus
    reason_codes: List[str] = Field(default_factory=list)
    explanation: str
    recommended_actions: List[str] = Field(default_factory=list)
    suggested_follow_up_days: int
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    dismissal_reason: Optional[str] = None
    dismissal_notes: Optional[str] = None
    intervention_id: Optional[str] = None
    signals_summary: Dict[str, Any] = Field(default_factory=dict)
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None

    @classmethod
    def from_model(cls, model: InterventionRecommendation) -> "RecommendationResponse":
        return cls(**model.model_dump())
