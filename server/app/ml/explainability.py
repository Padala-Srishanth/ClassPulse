"""
app.ml.explainability — Structured Explainability & Reason Generator
"""

from __future__ import annotations

from typing import List
from pydantic import BaseModel

from app.ml.anomaly import AnomalyReport
from app.ml.baseline import StudentBaseline
from app.ml.scoring import RiskLevel, RiskScoreOutput
from app.ml.trends import TrendSummary


class SignalReason(BaseModel):
    """Structured, verifiable reason explaining a component of the risk decision."""

    signal_type: str             # e.g., "ATTENDANCE_DECLINE", "HOMEWORK_DECLINE"
    metric: str                  # e.g., "attendance_rate", "homework_completion_rate"
    baseline_value: float
    current_value: float
    change: float
    severity: str                # "LOW" | "MEDIUM" | "HIGH"
    explanation: str             # Human-readable sentence


class ExplainabilityEngine:
    """Generates factual, feature-backed explanations for student risk status."""

    @classmethod
    def generate_reasons(
        cls,
        baseline: StudentBaseline,
        trends: TrendSummary,
        anomaly: AnomalyReport,
        score_output: RiskScoreOutput,
    ) -> List[SignalReason]:
        reasons: List[SignalReason] = []

        if score_output.risk_level == RiskLevel.INSUFFICIENT_DATA:
            reasons.append(
                SignalReason(
                    signal_type="INSUFFICIENT_HISTORY",
                    metric="total_weeks",
                    baseline_value=0.0,
                    current_value=float(baseline.total_weeks_observed),
                    change=0.0,
                    severity="LOW",
                    explanation="Insufficient historical baseline weeks to reliably detect academic decline.",
                )
            )
            return reasons

        # 1. Attendance Reason
        if (
            trends.is_attendance_declining
            and baseline.baseline_attendance_rate is not None
            and trends.recent_attendance_rate is not None
            and trends.attendance_delta is not None
        ):
            drop = abs(trends.attendance_delta)
            sev = "HIGH" if drop >= 25.0 else ("MEDIUM" if drop >= 15.0 else "LOW")
            reasons.append(
                SignalReason(
                    signal_type="ATTENDANCE_DECLINE",
                    metric="attendance_rate",
                    baseline_value=baseline.baseline_attendance_rate,
                    current_value=trends.recent_attendance_rate,
                    change=trends.attendance_delta,
                    severity=sev,
                    explanation=(
                        f"Attendance decreased by {drop:.1f} percentage points from historical "
                        f"baseline ({baseline.baseline_attendance_rate:.1f}% → {trends.recent_attendance_rate:.1f}%)."
                    ),
                )
            )

        # 2. Homework Reason
        if (
            trends.is_homework_declining
            and baseline.baseline_homework_completion_rate is not None
            and trends.recent_homework_completion_rate is not None
            and trends.homework_delta is not None
        ):
            drop = abs(trends.homework_delta)
            sev = "HIGH" if drop >= 30.0 else ("MEDIUM" if drop >= 20.0 else "LOW")
            reasons.append(
                SignalReason(
                    signal_type="HOMEWORK_DECLINE",
                    metric="homework_completion_rate",
                    baseline_value=baseline.baseline_homework_completion_rate,
                    current_value=trends.recent_homework_completion_rate,
                    change=trends.homework_delta,
                    severity=sev,
                    explanation=(
                        f"Homework completion rate dropped by {drop:.1f} percentage points from baseline "
                        f"({baseline.baseline_homework_completion_rate:.1f}% → {trends.recent_homework_completion_rate:.1f}%)."
                    ),
                )
            )

        # 3. Test Score Reason
        if (
            trends.is_test_declining
            and baseline.baseline_test_average is not None
            and trends.recent_test_average is not None
            and trends.test_delta is not None
        ):
            drop = abs(trends.test_delta)
            sev = "HIGH" if drop >= 20.0 else ("MEDIUM" if drop >= 15.0 else "LOW")
            reasons.append(
                SignalReason(
                    signal_type="TEST_SCORE_DECLINE",
                    metric="test_average",
                    baseline_value=baseline.baseline_test_average,
                    current_value=trends.recent_test_average,
                    change=trends.test_delta,
                    severity=sev,
                    explanation=(
                        f"Average test score dropped by {drop:.1f} percentage points below baseline "
                        f"({baseline.baseline_test_average:.1f}% → {trends.recent_test_average:.1f}%)."
                    ),
                )
            )

        # 4. Persistence Reason
        if trends.consecutive_dropping_weeks >= 2:
            reasons.append(
                SignalReason(
                    signal_type="PERSISTENT_DECLINE",
                    metric="consecutive_dropping_weeks",
                    baseline_value=0.0,
                    current_value=float(trends.consecutive_dropping_weeks),
                    change=float(trends.consecutive_dropping_weeks),
                    severity="HIGH" if trends.consecutive_dropping_weeks >= 3 else "MEDIUM",
                    explanation=(
                        f"Decline in engagement has persisted across {trends.consecutive_dropping_weeks} consecutive weeks."
                    ),
                )
            )

        # 5. Cross-Signal Agreement Reason
        if trends.multi_signal_decline_count >= 2:
            reasons.append(
                SignalReason(
                    signal_type="MULTI_SIGNAL_AGREEMENT",
                    metric="declining_signals_count",
                    baseline_value=0.0,
                    current_value=float(trends.multi_signal_decline_count),
                    change=float(trends.multi_signal_decline_count),
                    severity="HIGH",
                    explanation=(
                        f"Multiple distinct indicators ({trends.multi_signal_decline_count} signals) are declining simultaneously."
                    ),
                )
            )

        # 6. Fallback if score is LOW and no major declines were flagged
        if not reasons and score_output.risk_level == RiskLevel.LOW:
            reasons.append(
                SignalReason(
                    signal_type="STABLE_PERFORMANCE",
                    metric="risk_score",
                    baseline_value=0.0,
                    current_value=score_output.risk_score,
                    change=0.0,
                    severity="LOW",
                    explanation="Student engagement and performance metrics are stable within historical baseline ranges.",
                )
            )

        return reasons
