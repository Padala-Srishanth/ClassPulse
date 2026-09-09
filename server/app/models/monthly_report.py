"""
app.models.monthly_report — Monthly Report Domain Models
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DataStatus(str, Enum):
    SUFFICIENT_DATA = "SUFFICIENT_DATA"
    PARTIAL_DATA = "PARTIAL_DATA"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NO_DATA = "NO_DATA"


class TrendDirection(str, Enum):
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    DECLINING = "DECLINING"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"


class MonthlyStudentReport(BaseModel):
    """Aggregated monthly performance & risk report for an individual student."""

    id: str                                  # {student_id}_{report_period}
    school_id: str
    class_id: str
    student_id: str
    student_name: str
    student_code: str = ""
    report_period: str                       # YYYY-MM
    year: int
    month: int
    generated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    data_status: DataStatus = DataStatus.SUFFICIENT_DATA

    # Sub-sections
    attendance: Dict[str, Any] = Field(default_factory=dict)
    homework: Dict[str, Any] = Field(default_factory=dict)
    academic: Dict[str, Any] = Field(default_factory=dict)
    risk: Dict[str, Any] = Field(default_factory=dict)
    trends: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "MonthlyStudentReport":
        data = dict(data)
        data["id"] = doc_id
        if "generated_at" in data and hasattr(data["generated_at"], "timestamp"):
            from datetime import datetime as dt
            data["generated_at"] = dt.fromtimestamp(data["generated_at"].timestamp(), tz=timezone.utc)
        return cls(**data)

    def to_firestore(self) -> dict:
        d = self.model_dump(exclude={"id"}, mode="json")
        d["data_status"] = self.data_status.value
        return d


class MonthlyClassReport(BaseModel):
    """Aggregated monthly performance & risk report for a class cohort."""

    id: str                                  # {class_id}_{report_period}
    school_id: str
    class_id: str
    class_name: str = ""
    grade: str = ""
    section: str = ""
    report_period: str                       # YYYY-MM
    year: int
    month: int
    generated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    data_status: DataStatus = DataStatus.SUFFICIENT_DATA

    total_students: int = 0
    total_students_with_data: int = 0
    average_attendance: Optional[float] = None
    average_academic_percentage: Optional[float] = None
    subject_wise_average: Dict[str, float] = Field(default_factory=dict)
    average_homework_completion: Optional[float] = None

    # Risk distribution
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    needs_data_count: int = 0

    trends: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "MonthlyClassReport":
        data = dict(data)
        data["id"] = doc_id
        if "generated_at" in data and hasattr(data["generated_at"], "timestamp"):
            from datetime import datetime as dt
            data["generated_at"] = dt.fromtimestamp(data["generated_at"].timestamp(), tz=timezone.utc)
        return cls(**data)

    def to_firestore(self) -> dict:
        d = self.model_dump(exclude={"id"}, mode="json")
        d["data_status"] = self.data_status.value
        return d


class MonthlySchoolReport(BaseModel):
    """School-wide aggregated monthly report for principals and school admins."""

    id: str                                  # {school_id}_{report_period}
    school_id: str
    school_name: str = ""
    report_period: str                       # YYYY-MM
    year: int
    month: int
    generated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    data_status: DataStatus = DataStatus.SUFFICIENT_DATA

    total_students: int = 0
    total_classes: int = 0
    average_attendance: Optional[float] = None
    average_academic_percentage: Optional[float] = None

    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    needs_data_count: int = 0

    class_comparisons: List[Dict[str, Any]] = Field(default_factory=list)
    student_risk_leaderboard: List[Dict[str, Any]] = Field(default_factory=list)
    monthly_interventions: Dict[str, Any] = Field(default_factory=dict)
    trends: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "MonthlySchoolReport":
        data = dict(data)
        data["id"] = doc_id
        if "generated_at" in data and hasattr(data["generated_at"], "timestamp"):
            from datetime import datetime as dt
            data["generated_at"] = dt.fromtimestamp(data["generated_at"].timestamp(), tz=timezone.utc)
        return cls(**data)

    def to_firestore(self) -> dict:
        d = self.model_dump(exclude={"id"}, mode="json")
        d["data_status"] = self.data_status.value
        return d
