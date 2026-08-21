"""
app.ml.features — Weekly Engagement Signature & Feature Engineering
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel

from app.models.academic import (
    AttendanceRecord,
    AttendanceStatus,
    HomeworkRecord,
    HomeworkStatus,
    TestScoreRecord,
)


class WeeklyEngagementSignature(BaseModel):
    """Weekly aggregated metrics for a single student."""

    week_key: str  # ISO calendar week: "YYYY-Www"
    
    # Attendance
    attendance_rate: Optional[float] = None       # 0.0 - 100.0 (None if 0 records)
    attendance_present_count: int = 0
    attendance_total_count: int = 0

    # Homework
    homework_completion_rate: Optional[float] = None  # 0.0 - 100.0 (None if 0 assignments)
    homework_completed_count: int = 0
    homework_total_count: int = 0

    # Tests
    average_test_percentage: Optional[float] = None   # 0.0 - 100.0 (None if 0 tests)
    test_count: int = 0


def get_iso_week(date_str: str) -> str:
    """Convert YYYY-MM-DD string to ISO calendar week key 'YYYY-Www'."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    year, week_num, _ = dt.isocalendar()
    return f"{year}-W{week_num:02d}"


class FeatureExtractor:
    """Extracts weekly engagement signatures from raw academic records."""

    @classmethod
    def build_weekly_signatures(
        cls,
        attendance_records: List[AttendanceRecord],
        homework_records: List[HomeworkRecord],
        test_records: List[TestScoreRecord],
    ) -> List[WeeklyEngagementSignature]:
        """
        Aggregate attendance, homework, and test score records by ISO week.
        Returns a sorted list of WeeklyEngagementSignature objects.
        """
        weeks_map: Dict[str, Dict] = {}

        def _get_week_dict(week_key: str) -> Dict:
            if week_key not in weeks_map:
                weeks_map[week_key] = {
                    "att_present": 0,
                    "att_total": 0,
                    "hw_completed": 0,
                    "hw_total": 0,
                    "test_percentages": [],
                }
            return weeks_map[week_key]

        # 1. Process Attendance
        for att in attendance_records:
            try:
                wk = get_iso_week(att.date)
            except Exception:
                continue
            w_data = _get_week_dict(wk)
            w_data["att_total"] += 1
            if att.status == AttendanceStatus.PRESENT:
                w_data["att_present"] += 1
            elif att.status == AttendanceStatus.LATE:
                # Late counts as partial presence (0.5)
                w_data["att_present"] += 0.5

        # 2. Process Homework
        for hw in homework_records:
            try:
                wk = get_iso_week(hw.assignment_date)
            except Exception:
                continue
            w_data = _get_week_dict(wk)
            w_data["hw_total"] += 1
            if hw.status == HomeworkStatus.COMPLETED:
                w_data["hw_completed"] += 1
            elif hw.status == HomeworkStatus.LATE:
                # Late homework counts as 0.5 completion
                w_data["hw_completed"] += 0.5

        # 3. Process Test Scores
        for ts in test_records:
            try:
                wk = get_iso_week(ts.assessment_date)
            except Exception:
                continue
            w_data = _get_week_dict(wk)
            w_data["test_percentages"].append(ts.percentage)

        # 4. Construct sorted signatures
        signatures: List[WeeklyEngagementSignature] = []
        for week_key in sorted(weeks_map.keys()):
            w_data = weeks_map[week_key]

            att_rate = None
            if w_data["att_total"] > 0:
                att_rate = round((w_data["att_present"] / w_data["att_total"]) * 100.0, 2)

            hw_rate = None
            if w_data["hw_total"] > 0:
                hw_rate = round((w_data["hw_completed"] / w_data["hw_total"]) * 100.0, 2)

            test_avg = None
            if len(w_data["test_percentages"]) > 0:
                test_avg = round(
                    sum(w_data["test_percentages"]) / len(w_data["test_percentages"]), 2
                )

            signatures.append(
                WeeklyEngagementSignature(
                    week_key=week_key,
                    attendance_rate=att_rate,
                    attendance_present_count=int(w_data["att_present"]),
                    attendance_total_count=w_data["att_total"],
                    homework_completion_rate=hw_rate,
                    homework_completed_count=int(w_data["hw_completed"]),
                    homework_total_count=w_data["hw_total"],
                    average_test_percentage=test_avg,
                    test_count=len(w_data["test_percentages"]),
                )
            )

        return signatures
