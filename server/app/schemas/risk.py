"""
app.schemas.risk — Risk Analysis API Request & Response Schemas
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.ml.explainability import SignalReason
from app.ml.features import WeeklyEngagementSignature
from app.ml.scoring import RiskLevel
from app.models.risk_alert import AlertStatus


class RiskAlertResponse(BaseModel):
    id: str
    school_id: str
    class_id: str
    student_id: str
    risk_score: float
    risk_level: RiskLevel
    model_version: str
    reasons: List[SignalReason]
    signals: Dict[str, Any]
    analysis_period: str
    status: AlertStatus
    created_at: str

    @classmethod
    def from_model(cls, alert) -> "RiskAlertResponse":
        return cls(
            id=alert.id,
            school_id=alert.school_id,
            class_id=alert.class_id,
            student_id=alert.student_id,
            risk_score=alert.risk_score,
            risk_level=alert.risk_level,
            model_version=alert.model_version,
            reasons=[SignalReason(**r) for r in alert.reasons],
            signals=alert.signals,
            analysis_period=alert.analysis_period,
            status=alert.status,
            created_at=alert.created_at.isoformat(),
        )


class StudentRiskAnalysisResponse(BaseModel):
    student_id: str
    school_id: str
    class_id: str
    risk_score: float
    risk_level: RiskLevel
    model_version: str
    analysis_period: str
    reasons: List[SignalReason]
    weekly_signatures: List[WeeklyEngagementSignature]
    baseline: Dict[str, Any]
    trends: Dict[str, Any]
    alert: Optional[RiskAlertResponse] = None


class ClassRiskSummaryResponse(BaseModel):
    class_id: str
    school_id: str
    total_students: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    insufficient_data_count: int
    alerts: List[RiskAlertResponse]
