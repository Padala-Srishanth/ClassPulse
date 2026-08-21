"""
app.models.risk_alert — Risk Alert Domain Model
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.ml.scoring import RiskLevel


class AlertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class RiskAlert(BaseModel):
    """Domain model representing a generated early-warning risk alert stored in Firestore."""

    id: str
    school_id: str
    class_id: str
    student_id: str
    risk_score: float
    risk_level: RiskLevel
    model_version: str
    reasons: List[Dict[str, Any]] = Field(default_factory=list)
    signals: Dict[str, Any] = Field(default_factory=dict)
    analysis_period: str         # e.g., "2024-W36"
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "RiskAlert":
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
        d["risk_level"] = self.risk_level.value
        d["status"] = self.status.value
        return d
