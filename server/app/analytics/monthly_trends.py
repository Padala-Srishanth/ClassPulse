"""
app.analytics.monthly_trends — Month-over-Month Trend Evaluation
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from app.models.monthly_report import TrendDirection


class MonthlyTrendAnalyzer:
    """Analyzes month-over-month trends for attendance, homework, academic, and risk."""

    THRESHOLD = 3.0  # Percentage points threshold for improving/declining

    @classmethod
    def evaluate_metric_trend(
        cls,
        current_val: Optional[float],
        prev_val: Optional[float],
        lower_is_better: bool = False,
    ) -> tuple[Optional[float], TrendDirection]:
        if current_val is None or prev_val is None:
            return None, TrendDirection.INSUFFICIENT_HISTORY

        delta = round(current_val - prev_val, 2)
        if lower_is_better:
            if delta <= -cls.THRESHOLD:
                return delta, TrendDirection.IMPROVING
            elif delta >= cls.THRESHOLD:
                return delta, TrendDirection.DECLINING
            else:
                return delta, TrendDirection.STABLE
        else:
            if delta >= cls.THRESHOLD:
                return delta, TrendDirection.IMPROVING
            elif delta <= -cls.THRESHOLD:
                return delta, TrendDirection.DECLINING
            else:
                return delta, TrendDirection.STABLE

    @classmethod
    def compute_trends(
        cls,
        current_attendance_pct: Optional[float],
        current_homework_pct: Optional[float],
        current_academic_pct: Optional[float],
        prev_report: Optional[Dict[str, Any]] = None,
        historical_reports: Optional[List[Dict[str, Any]]] = None,
        current_risk_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        if not prev_report:
            return {
                "previous_period": None,
                "attendance_delta": None,
                "attendance_direction": TrendDirection.INSUFFICIENT_HISTORY.value,
                "homework_delta": None,
                "homework_direction": TrendDirection.INSUFFICIENT_HISTORY.value,
                "academic_delta": None,
                "academic_direction": TrendDirection.INSUFFICIENT_HISTORY.value,
                "risk_delta": None,
                "risk_direction": TrendDirection.INSUFFICIENT_HISTORY.value,
                "overall_direction": TrendDirection.INSUFFICIENT_HISTORY.value,
                "consecutive_declining_months": 0,
            }

        prev_period = prev_report.get("report_period")
        prev_att = prev_report.get("attendance", {}).get("attendance_percentage")
        prev_hw = prev_report.get("homework", {}).get("completion_rate")
        prev_acad = prev_report.get("academic", {}).get("average_percentage")
        prev_risk = prev_report.get("risk", {}).get("risk_score")

        att_delta, att_dir = cls.evaluate_metric_trend(current_attendance_pct, prev_att)
        hw_delta, hw_dir = cls.evaluate_metric_trend(current_homework_pct, prev_hw)
        acad_delta, acad_dir = cls.evaluate_metric_trend(current_academic_pct, prev_acad)
        risk_delta, risk_dir = cls.evaluate_metric_trend(current_risk_score, prev_risk, lower_is_better=True)

        # Count declining signals
        declining_count = sum(1 for d in [att_dir, hw_dir, acad_dir] if d == TrendDirection.DECLINING)
        improving_count = sum(1 for d in [att_dir, hw_dir, acad_dir] if d == TrendDirection.IMPROVING)

        if declining_count > improving_count:
            overall_dir = TrendDirection.DECLINING
        elif improving_count > declining_count:
            overall_dir = TrendDirection.IMPROVING
        elif att_dir == TrendDirection.INSUFFICIENT_HISTORY and hw_dir == TrendDirection.INSUFFICIENT_HISTORY and acad_dir == TrendDirection.INSUFFICIENT_HISTORY:
            overall_dir = TrendDirection.INSUFFICIENT_HISTORY
        else:
            overall_dir = TrendDirection.STABLE

        # Calculate consecutive declining months across past history
        consecutive_declines = 1 if overall_dir == TrendDirection.DECLINING else 0
        if consecutive_declines > 0 and historical_reports:
            # Iterate backwards through historical reports
            for h in reversed(historical_reports):
                h_trends = h.get("trends", {})
                if h_trends.get("overall_direction") == TrendDirection.DECLINING.value:
                    consecutive_declines += 1
                else:
                    break

        return {
            "previous_period": prev_period,
            "attendance_delta": att_delta,
            "attendance_direction": att_dir.value,
            "homework_delta": hw_delta,
            "homework_direction": hw_dir.value,
            "academic_delta": acad_delta,
            "academic_direction": acad_dir.value,
            "risk_delta": risk_delta,
            "risk_direction": risk_dir.value,
            "overall_direction": overall_dir.value,
            "consecutive_declining_months": consecutive_declines,
        }
