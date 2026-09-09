"""
app.analytics.monthly_risk — Monthly Risk Scoring & Explainability Engine
"""

from __future__ import annotations

import statistics
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.models.academic import AttendanceRecord, AttendanceStatus, HomeworkRecord, HomeworkStatus, TestScoreRecord
from app.models.monthly_report import DataStatus


class MonthlyBaseline(BaseModel):
    has_sufficient_history: bool
    months_observed: int
    baseline_attendance: Optional[float] = None
    baseline_homework: Optional[float] = None
    baseline_academic: Optional[float] = None


class MonthlyRiskOutput(BaseModel):
    risk_score: Optional[float] = None
    risk_level: str  # "LOW" | "MEDIUM" | "HIGH" | "INSUFFICIENT_DATA" | "NO_DATA"
    subscores: Dict[str, float]
    multipliers: Dict[str, float]
    baseline_used: Dict[str, Any]
    risk_factors: List[str]
    positive_highlights: List[str]
    recommended_interventions: List[str]


class MonthlyRiskCalculator:
    """Computes monthly drop-based risk score with baseline comparisons and transparent explainability."""

    WEIGHT_ATTENDANCE = 0.35
    WEIGHT_HOMEWORK = 0.30
    WEIGHT_ACADEMIC = 0.35

    @classmethod
    def compute_historical_baseline(
        cls,
        prior_reports: List[Dict[str, Any]],
        prior_attendance: Optional[List[AttendanceRecord]] = None,
        prior_homework: Optional[List[HomeworkRecord]] = None,
        prior_tests: Optional[List[TestScoreRecord]] = None,
    ) -> MonthlyBaseline:
        # First try to aggregate from prior monthly reports
        valid_reports = [r for r in prior_reports if r.get("data_status") in ("SUFFICIENT_DATA", "PARTIAL_DATA")]
        if valid_reports:
            att_vals = [r["attendance"]["attendance_percentage"] for r in valid_reports if r.get("attendance", {}).get("attendance_percentage") is not None]
            hw_vals = [r["homework"]["completion_rate"] for r in valid_reports if r.get("homework", {}).get("completion_rate") is not None]
            acad_vals = [r["academic"]["average_percentage"] for r in valid_reports if r.get("academic", {}).get("average_percentage") is not None]

            avg_att = round(statistics.mean(att_vals), 2) if att_vals else None
            avg_hw = round(statistics.mean(hw_vals), 2) if hw_vals else None
            avg_acad = round(statistics.mean(acad_vals), 2) if acad_vals else None

            return MonthlyBaseline(
                has_sufficient_history=len(valid_reports) >= 1,
                months_observed=len(valid_reports),
                baseline_attendance=avg_att,
                baseline_homework=avg_hw,
                baseline_academic=avg_acad,
            )

        # Fallback to prior raw records
        if prior_attendance or prior_homework or prior_tests:
            att_pct = None
            if prior_attendance:
                days = len(prior_attendance)
                pres = sum(1 for r in prior_attendance if r.status == AttendanceStatus.PRESENT)
                late = sum(1 for r in prior_attendance if r.status == AttendanceStatus.LATE)
                att_pct = round(((pres + 0.5 * late) / days) * 100, 2) if days > 0 else None

            hw_pct = None
            if prior_homework:
                tot = len(prior_homework)
                comp = sum(1 for r in prior_homework if r.status == HomeworkStatus.COMPLETED)
                late_hw = sum(1 for r in prior_homework if r.status == HomeworkStatus.LATE)
                hw_pct = round(((comp + 0.5 * late_hw) / tot) * 100, 2) if tot > 0 else None

            acad_pct = None
            if prior_tests:
                scores = [t.percentage for t in prior_tests]
                acad_pct = round(statistics.mean(scores), 2) if scores else None

            has_hist = bool(att_pct is not None or hw_pct is not None or acad_pct is not None)
            return MonthlyBaseline(
                has_sufficient_history=has_hist,
                months_observed=1 if has_hist else 0,
                baseline_attendance=att_pct,
                baseline_homework=hw_pct,
                baseline_academic=acad_pct,
            )

        return MonthlyBaseline(
            has_sufficient_history=False,
            months_observed=0,
            baseline_attendance=None,
            baseline_homework=None,
            baseline_academic=None,
        )

    @classmethod
    def evaluate_monthly_risk(
        cls,
        data_status: DataStatus,
        attendance_percentage: Optional[float],
        homework_completion_rate: Optional[float],
        academic_percentage: Optional[float],
        baseline: MonthlyBaseline,
        consecutive_declining_months: int = 0,
    ) -> MonthlyRiskOutput:
        # 1. Check for missing / insufficient data
        if data_status == DataStatus.NO_DATA:
            return MonthlyRiskOutput(
                risk_score=None,
                risk_level="NO_DATA",
                subscores={"attendance_drop": 0.0, "homework_drop": 0.0, "academic_drop": 0.0},
                multipliers={"persistence": 1.0, "cross_signal": 1.0},
                baseline_used=baseline.model_dump(),
                risk_factors=["No academic records were logged for this month."],
                positive_highlights=[],
                recommended_interventions=["Request updated attendance, homework, and assessment data."],
            )

        if data_status == DataStatus.INSUFFICIENT_DATA:
            return MonthlyRiskOutput(
                risk_score=None,
                risk_level="INSUFFICIENT_DATA",
                subscores={"attendance_drop": 0.0, "homework_drop": 0.0, "academic_drop": 0.0},
                multipliers={"persistence": 1.0, "cross_signal": 1.0},
                baseline_used=baseline.model_dump(),
                risk_factors=["Insufficient records logged to establish a statistically reliable monthly risk score."],
                positive_highlights=[],
                recommended_interventions=["Ensure daily attendance and submissions are recorded."],
            )

        # 2. Determine effective baselines (if no prior history, use current as baseline => drop is 0)
        eff_base_att = baseline.baseline_attendance if baseline.baseline_attendance is not None else attendance_percentage
        eff_base_hw = baseline.baseline_homework if baseline.baseline_homework is not None else homework_completion_rate
        eff_base_acad = baseline.baseline_academic if baseline.baseline_academic is not None else academic_percentage

        # 3. Compute drops from baseline (magnitude of decline, clamped to min 0)
        att_delta = round(attendance_percentage - eff_base_att, 2) if (attendance_percentage is not None and eff_base_att is not None) else None
        hw_delta = round(homework_completion_rate - eff_base_hw, 2) if (homework_completion_rate is not None and eff_base_hw is not None) else None
        acad_delta = round(academic_percentage - eff_base_acad, 2) if (academic_percentage is not None and eff_base_acad is not None) else None

        att_drop = abs(min(0.0, att_delta)) if att_delta is not None else 0.0
        hw_drop = abs(min(0.0, hw_delta)) if hw_delta is not None else 0.0
        acad_drop = abs(min(0.0, acad_delta)) if acad_delta is not None else 0.0

        # Subscores
        subscores = {
            "attendance_drop": round(att_drop, 2),
            "homework_drop": round(hw_drop, 2),
            "academic_drop": round(acad_drop, 2),
        }

        # 4. Dynamic weight normalization across present signals
        active_weights = []
        active_drops = []

        if attendance_percentage is not None and eff_base_att is not None:
            active_weights.append(cls.WEIGHT_ATTENDANCE)
            active_drops.append(att_drop)

        if homework_completion_rate is not None and eff_base_hw is not None:
            active_weights.append(cls.WEIGHT_HOMEWORK)
            active_drops.append(hw_drop)

        if academic_percentage is not None and eff_base_acad is not None:
            active_weights.append(cls.WEIGHT_ACADEMIC)
            active_drops.append(acad_drop)

        if not active_weights or sum(active_weights) == 0.0:
            weighted_base_score = 0.0
        else:
            total_weight = sum(active_weights)
            weighted_base_score = sum(d * (w / total_weight) for d, w in zip(active_drops, active_weights))

        # 5. Multipliers
        persistence_mult = 1.2 if consecutive_declining_months >= 2 else 1.0

        # Significant decline across 2+ signals (drop >= 5.0)
        signals_dropping = sum(1 for d in [att_drop, hw_drop, acad_drop] if d >= 5.0)
        cross_signal_mult = 1.2 if signals_dropping >= 2 else 1.0

        raw_score = weighted_base_score * persistence_mult * cross_signal_mult
        final_risk_score = round(min(100.0, max(0.0, raw_score)), 1)

        # 6. Risk Level
        if final_risk_score <= 20.0:
            level = "LOW"
        elif final_risk_score <= 50.0:
            level = "MEDIUM"
        else:
            level = "HIGH"

        # 7. Explainability & Insights
        risk_factors = []
        positive_highlights = []
        interventions = []

        if att_delta is not None:
            if att_delta <= -5.0:
                risk_factors.append(f"Attendance dropped by {abs(att_delta):.1f}% from historical baseline ({eff_base_att:.1f}%).")
                interventions.append("Schedule attendance counselor meeting and notify parents.")
            elif attendance_percentage >= 90.0:
                positive_highlights.append(f"Consistent high attendance at {attendance_percentage:.1f}%.")

        if hw_delta is not None:
            if hw_delta <= -10.0:
                risk_factors.append(f"Homework completion decreased by {abs(hw_delta):.1f}% below baseline ({eff_base_hw:.1f}%).")
                interventions.append("Assign structured homework check-in and peer study partner.")
            elif homework_completion_rate >= 90.0:
                positive_highlights.append(f"Strong assignment completion rate of {homework_completion_rate:.1f}%.")

        if acad_delta is not None:
            if acad_delta <= -8.0:
                risk_factors.append(f"Academic test average dropped by {abs(acad_delta):.1f}% compared to baseline ({eff_base_acad:.1f}%).")
                interventions.append("Offer targeted subject tutoring sessions and revision worksheets.")
            elif academic_percentage >= 85.0:
                positive_highlights.append(f"Strong academic performance with test average at {academic_percentage:.1f}%.")
            elif acad_delta >= 3.0:
                positive_highlights.append(f"Academic marks improved by {acad_delta:.1f}% over baseline.")

        if consecutive_declining_months >= 2:
            risk_factors.append(f"Persistent performance decline observed over {consecutive_declining_months} consecutive months.")
            interventions.append("Conduct comprehensive multi-teacher academic intervention review.")

        if signals_dropping >= 2:
            risk_factors.append(f"Compound decline detected across {signals_dropping} distinct performance signals.")

        if level == "LOW" and not risk_factors:
            risk_factors.append("Performance is steady with no significant drops from baseline.")
            positive_highlights.append("All engagement signals within normal, healthy parameters.")

        if not interventions:
            if level == "LOW":
                interventions.append("Continue standard positive reinforcement and regular monitoring.")
            else:
                interventions.append("Monitor student trajectory closely in upcoming weekly checks.")

        return MonthlyRiskOutput(
            risk_score=final_risk_score,
            risk_level=level,
            subscores=subscores,
            multipliers={
                "persistence": persistence_mult,
                "cross_signal": cross_signal_mult,
            },
            baseline_used=baseline.model_dump(),
            risk_factors=risk_factors,
            positive_highlights=positive_highlights,
            recommended_interventions=interventions,
        )
