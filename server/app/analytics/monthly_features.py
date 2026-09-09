"""
app.analytics.monthly_features — Monthly Student Feature Extraction
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.models.academic import AttendanceRecord, AttendanceStatus, HomeworkRecord, HomeworkStatus, TestScoreRecord
from app.models.monthly_report import DataStatus


class MonthlyStudentFeatures(BaseModel):
    report_period: str  # YYYY-MM
    year: int
    month: int
    data_status: DataStatus

    attendance: Dict[str, Any]
    homework: Dict[str, Any]
    academic: Dict[str, Any]


class MonthlyFeatureExtractor:
    """Extracts monthly metrics for a single student over a YYYY-MM period."""

    @classmethod
    def extract_monthly_features(
        cls,
        report_period: str,
        attendance_records: List[AttendanceRecord],
        homework_records: List[HomeworkRecord],
        test_records: List[TestScoreRecord],
    ) -> MonthlyStudentFeatures:
        year, month = map(int, report_period.split("-"))

        # 1. Filter by YYYY-MM prefix
        month_prefix = f"{report_period}-"
        m_att = [r for r in attendance_records if r.date.startswith(report_period)]
        m_hw = [r for r in homework_records if r.assignment_date.startswith(report_period)]
        m_tests = [r for r in test_records if r.assessment_date.startswith(report_period)]

        # 2. Attendance aggregation
        total_school_days = len(m_att)
        days_present = sum(1 for r in m_att if r.status == AttendanceStatus.PRESENT)
        days_absent = sum(1 for r in m_att if r.status == AttendanceStatus.ABSENT)
        days_late = sum(1 for r in m_att if r.status == AttendanceStatus.LATE)
        days_excused = sum(1 for r in m_att if r.status == AttendanceStatus.EXCUSED)

        attendance_percentage: Optional[float] = None
        if total_school_days > 0:
            effective_present = days_present + (0.5 * days_late)
            attendance_percentage = round((effective_present / total_school_days) * 100, 2)

        attendance_dict = {
            "total_school_days": total_school_days,
            "days_present": days_present,
            "days_absent": days_absent,
            "days_late": days_late,
            "days_excused": days_excused,
            "attendance_percentage": attendance_percentage,
        }

        # 3. Homework aggregation
        total_assignments = len(m_hw)
        completed_hw = sum(1 for r in m_hw if r.status == HomeworkStatus.COMPLETED)
        not_completed_hw = sum(1 for r in m_hw if r.status == HomeworkStatus.NOT_COMPLETED)
        late_hw = sum(1 for r in m_hw if r.status == HomeworkStatus.LATE)

        completion_rate: Optional[float] = None
        if total_assignments > 0:
            effective_completed = completed_hw + (0.5 * late_hw)
            completion_rate = round((effective_completed / total_assignments) * 100, 2)

        homework_dict = {
            "total_assignments": total_assignments,
            "completed": completed_hw,
            "not_completed": not_completed_hw,
            "late": late_hw,
            "completion_rate": completion_rate,
        }

        # 4. Academic / Test aggregation
        total_tests = len(m_tests)
        subject_breakdown: Dict[str, Dict[str, Any]] = {}
        all_percentages: List[float] = []

        for t in m_tests:
            pct = t.percentage
            all_percentages.append(pct)
            subj = t.subject or "General"
            if subj not in subject_breakdown:
                subject_breakdown[subj] = {
                    "tests_count": 0,
                    "scores": [],
                    "average_percentage": 0.0,
                    "highest_percentage": 0.0,
                    "lowest_percentage": 100.0,
                }
            sb = subject_breakdown[subj]
            sb["tests_count"] += 1
            sb["scores"].append(pct)
            sb["highest_percentage"] = max(sb["highest_percentage"], pct)
            sb["lowest_percentage"] = min(sb["lowest_percentage"], pct)

        for subj, sb in subject_breakdown.items():
            scores = sb.pop("scores")
            sb["average_percentage"] = round(sum(scores) / len(scores), 2) if scores else 0.0

        academic_percentage: Optional[float] = None
        if total_tests > 0 and all_percentages:
            academic_percentage = round(sum(all_percentages) / len(all_percentages), 2)

        academic_dict = {
            "total_tests": total_tests,
            "average_percentage": academic_percentage,
            "subject_breakdown": subject_breakdown,
        }

        # 5. Data Status evaluation
        total_records = total_school_days + total_assignments + total_tests
        if total_records == 0:
            data_status = DataStatus.NO_DATA
        elif total_school_days < 5 and total_records < 5:
            data_status = DataStatus.INSUFFICIENT_DATA
        elif total_school_days >= 8 and (total_assignments > 0 or total_tests > 0):
            data_status = DataStatus.SUFFICIENT_DATA
        else:
            data_status = DataStatus.PARTIAL_DATA

        return MonthlyStudentFeatures(
            report_period=report_period,
            year=year,
            month=month,
            data_status=data_status,
            attendance=attendance_dict,
            homework=homework_dict,
            academic=academic_dict,
        )
