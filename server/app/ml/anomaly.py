"""
app.ml.anomaly — Statistical Anomaly & Deviation Detector
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel

from app.ml.baseline import StudentBaseline
from app.ml.config import ml_settings
from app.ml.trends import TrendSummary


class AnomalyReport(BaseModel):
    """Statistical anomaly analysis comparing current observation against student distribution."""

    is_attendance_anomaly: bool = False
    attendance_z_score: Optional[float] = None

    is_homework_anomaly: bool = False
    homework_z_score: Optional[float] = None

    is_test_anomaly: bool = False
    test_z_score: Optional[float] = None

    has_any_anomaly: bool = False


class AnomalyDetector:
    """Detects statistical outliers and significant behavioral deviations from historical distribution."""

    @classmethod
    def detect_anomalies(
        cls,
        baseline: StudentBaseline,
        trends: TrendSummary,
    ) -> AnomalyReport:
        if not baseline.has_sufficient_history:
            return AnomalyReport()

        threshold = ml_settings.z_score_threshold

        # 1. Attendance Anomaly
        att_z = None
        is_att_anom = False
        if (
            trends.recent_attendance_rate is not None
            and baseline.baseline_attendance_rate is not None
        ):
            if baseline.baseline_attendance_std and baseline.baseline_attendance_std > 0:
                att_z = round(
                    (trends.recent_attendance_rate - baseline.baseline_attendance_rate)
                    / baseline.baseline_attendance_std,
                    2,
                )
                if att_z <= -threshold:
                    is_att_anom = True
            elif baseline.baseline_attendance_std == 0.0:
                # Zero variance in baseline (e.g., always 100%). Any significant drop is an anomaly.
                if trends.attendance_delta and trends.attendance_delta <= -ml_settings.significant_drop_attendance:
                    is_att_anom = True

        # 2. Homework Anomaly
        hw_z = None
        is_hw_anom = False
        if (
            trends.recent_homework_completion_rate is not None
            and baseline.baseline_homework_completion_rate is not None
        ):
            if baseline.baseline_homework_std and baseline.baseline_homework_std > 0:
                hw_z = round(
                    (trends.recent_homework_completion_rate - baseline.baseline_homework_completion_rate)
                    / baseline.baseline_homework_std,
                    2,
                )
                if hw_z <= -threshold:
                    is_hw_anom = True
            elif baseline.baseline_homework_std == 0.0:
                if trends.homework_delta and trends.homework_delta <= -ml_settings.significant_drop_homework:
                    is_hw_anom = True

        # 3. Test Score Anomaly
        test_z = None
        is_test_anom = False
        if (
            trends.recent_test_average is not None
            and baseline.baseline_test_average is not None
        ):
            if baseline.baseline_test_std and baseline.baseline_test_std > 0:
                test_z = round(
                    (trends.recent_test_average - baseline.baseline_test_average)
                    / baseline.baseline_test_std,
                    2,
                )
                if test_z <= -threshold:
                    is_test_anom = True
            elif baseline.baseline_test_std == 0.0:
                if trends.test_delta and trends.test_delta <= -ml_settings.significant_drop_test:
                    is_test_anom = True

        has_any = is_att_anom or is_hw_anom or is_test_anom

        return AnomalyReport(
            is_attendance_anomaly=is_att_anom,
            attendance_z_score=att_z,
            is_homework_anomaly=is_hw_anom,
            homework_z_score=hw_z,
            is_test_anomaly=is_test_anom,
            test_z_score=test_z,
            has_any_anomaly=has_any,
        )
