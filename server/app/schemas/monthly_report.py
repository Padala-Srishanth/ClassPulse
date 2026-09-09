"""
app.schemas.monthly_report — API Schemas for Monthly Reports & Historical Risk Analytics
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.monthly_report import (
    DataStatus,
    MonthlyClassReport,
    MonthlySchoolReport,
    MonthlyStudentReport,
    TrendDirection,
)


class GenerateMonthlyReportRequest(BaseModel):
    report_period: str = Field(..., description="Target month in YYYY-MM format (e.g. 2026-05)")


class MonthlyStudentReportResponse(BaseModel):
    id: str
    school_id: str
    class_id: str
    student_id: str
    student_name: str
    student_code: str = ""
    report_period: str
    year: int
    month: int
    generated_at: str
    data_status: DataStatus

    attendance: Dict[str, Any] = Field(default_factory=dict)
    homework: Dict[str, Any] = Field(default_factory=dict)
    academic: Dict[str, Any] = Field(default_factory=dict)
    risk: Dict[str, Any] = Field(default_factory=dict)
    trends: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_model(cls, model: MonthlyStudentReport) -> "MonthlyStudentReportResponse":
        return cls(
            id=model.id,
            school_id=model.school_id,
            class_id=model.class_id,
            student_id=model.student_id,
            student_name=model.student_name,
            student_code=model.student_code,
            report_period=model.report_period,
            year=model.year,
            month=model.month,
            generated_at=model.generated_at.isoformat() if hasattr(model.generated_at, "isoformat") else str(model.generated_at),
            data_status=model.data_status,
            attendance=model.attendance,
            homework=model.homework,
            academic=model.academic,
            risk=model.risk,
            trends=model.trends,
        )


class MonthlyClassReportResponse(BaseModel):
    id: str
    school_id: str
    class_id: str
    class_name: str = ""
    grade: str = ""
    section: str = ""
    report_period: str
    year: int
    month: int
    generated_at: str
    data_status: DataStatus

    total_students: int = 0
    total_students_with_data: int = 0
    average_attendance: Optional[float] = None
    average_academic_percentage: Optional[float] = None
    subject_wise_average: Dict[str, float] = Field(default_factory=dict)
    average_homework_completion: Optional[float] = None

    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    needs_data_count: int = 0

    trends: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_model(cls, model: MonthlyClassReport) -> "MonthlyClassReportResponse":
        return cls(
            id=model.id,
            school_id=model.school_id,
            class_id=model.class_id,
            class_name=model.class_name,
            grade=model.grade,
            section=model.section,
            report_period=model.report_period,
            year=model.year,
            month=model.month,
            generated_at=model.generated_at.isoformat() if hasattr(model.generated_at, "isoformat") else str(model.generated_at),
            data_status=model.data_status,
            total_students=model.total_students,
            total_students_with_data=model.total_students_with_data,
            average_attendance=model.average_attendance,
            average_academic_percentage=model.average_academic_percentage,
            subject_wise_average=model.subject_wise_average,
            average_homework_completion=model.average_homework_completion,
            high_risk_count=model.high_risk_count,
            medium_risk_count=model.medium_risk_count,
            low_risk_count=model.low_risk_count,
            needs_data_count=model.needs_data_count,
            trends=model.trends,
        )


class MonthlySchoolReportResponse(BaseModel):
    id: str
    school_id: str
    school_name: str = ""
    report_period: str
    year: int
    month: int
    generated_at: str
    data_status: DataStatus

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
    def from_model(cls, model: MonthlySchoolReport) -> "MonthlySchoolReportResponse":
        return cls(
            id=model.id,
            school_id=model.school_id,
            school_name=model.school_name,
            report_period=model.report_period,
            year=model.year,
            month=model.month,
            generated_at=model.generated_at.isoformat() if hasattr(model.generated_at, "isoformat") else str(model.generated_at),
            data_status=model.data_status,
            total_students=model.total_students,
            total_classes=model.total_classes,
            average_attendance=model.average_attendance,
            average_academic_percentage=model.average_academic_percentage,
            high_risk_count=model.high_risk_count,
            medium_risk_count=model.medium_risk_count,
            low_risk_count=model.low_risk_count,
            needs_data_count=model.needs_data_count,
            class_comparisons=model.class_comparisons,
            student_risk_leaderboard=model.student_risk_leaderboard,
            monthly_interventions=model.monthly_interventions,
            trends=model.trends,
        )
