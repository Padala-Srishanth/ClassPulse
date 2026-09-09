"""
app.models.intervention_recommendation — Smart Intervention Recommendation Domain Model
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.intervention import InterventionType


class PriorityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class RecommendationStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DISMISSED = "DISMISSED"
    CONVERTED_TO_INTERVENTION = "CONVERTED_TO_INTERVENTION"
    EXPIRED = "EXPIRED"


class RecommendationReasonCode(str, Enum):
    ATTENDANCE_DROP = "ATTENDANCE_DROP"
    HOMEWORK_DROP = "HOMEWORK_DROP"
    ACADEMIC_DROP = "ACADEMIC_DROP"
    MULTI_SIGNAL_DECLINE = "MULTI_SIGNAL_DECLINE"
    PERSISTENT_DECLINE = "PERSISTENT_DECLINE"
    SUDDEN_DROP = "SUDDEN_DROP"
    STABLE_LOW_PERFORMANCE = "STABLE_LOW_PERFORMANCE"
    RECOVERY_DETECTED = "RECOVERY_DETECTED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class DismissalReason(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ISSUE_ALREADY_RESOLVED = "ISSUE_ALREADY_RESOLVED"
    DUPLICATE_RECOMMENDATION = "DUPLICATE_RECOMMENDATION"
    TEACHER_JUDGMENT = "TEACHER_JUDGMENT"
    OTHER = "OTHER"


class InterventionRecommendation(BaseModel):
    """Domain model representing an explainable, deterministic intervention recommendation."""

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
    priority_score: float = 0.0
    status: RecommendationStatus = RecommendationStatus.PENDING
    reason_codes: List[str] = Field(default_factory=list)
    explanation: str
    recommended_actions: List[str] = Field(default_factory=list)
    suggested_follow_up_days: int = 7
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    dismissal_reason: Optional[str] = None
    dismissal_notes: Optional[str] = None
    intervention_id: Optional[str] = None
    signals_summary: Dict[str, Any] = Field(default_factory=dict)
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "InterventionRecommendation":
        d = dict(data)
        d["recommendation_id"] = doc_id
        for ts_field in ("created_at", "updated_at", "reviewed_at"):
            if ts_field in d and d[ts_field] is not None and hasattr(d[ts_field], "timestamp"):
                from datetime import datetime as dt
                d[ts_field] = dt.fromtimestamp(d[ts_field].timestamp(), tz=timezone.utc)
            elif ts_field in d and isinstance(d[ts_field], str):
                try:
                    d[ts_field] = datetime.fromisoformat(d[ts_field])
                except Exception:
                    pass
        return cls(**d)

    def to_firestore(self) -> dict:
        d = self.model_dump(exclude={"recommendation_id"}, mode="json")
        d["recommendation_type"] = self.recommendation_type.value
        d["priority_level"] = self.priority_level.value
        d["status"] = self.status.value
        return d
