"""
app.ml.scoring — Multi-Signal Risk Scoring Engine
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel

from app.ml.anomaly import AnomalyReport
from app.ml.baseline import StudentBaseline
from app.ml.config import ml_settings
from app.ml.trends import TrendSummary


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class RiskScoreOutput(BaseModel):
    """Result of risk score computation."""

    risk_score: float                  # 0.0 to 100.0
    risk_level: RiskLevel
    model_version: str

    # Signal Sub-scores (0.0 to 100.0)
    attendance_subscore: float = 0.0
    homework_subscore: float = 0.0
    test_subscore: float = 0.0

    # Multipliers applied
    applied_persistence_multiplier: float = 1.0
    applied_cross_signal_multiplier: float = 1.0


class RiskScorer:
    """Computes transparent, weighted multi-signal risk scores."""

    @classmethod
    def compute_risk(
        cls,
        baseline: StudentBaseline,
        trends: TrendSummary,
        anomaly: AnomalyReport,
    ) -> RiskScoreOutput:
        model_version = ml_settings.model_version

        # 1. Handle Insufficient History
        if not baseline.has_sufficient_history:
            return RiskScoreOutput(
                risk_score=0.0,
                risk_level=RiskLevel.INSUFFICIENT_DATA,
                model_version=model_version,
            )

        # 2. Compute individual signal drops (magnitude of decline from baseline, 0.0 if improved/stable)
        att_drop = abs(min(0.0, trends.attendance_delta)) if trends.attendance_delta is not None else 0.0
        hw_drop = abs(min(0.0, trends.homework_delta)) if trends.homework_delta is not None else 0.0
        test_drop = abs(min(0.0, trends.test_delta)) if trends.test_delta is not None else 0.0

        # Subscores correspond to raw drop magnitude
        att_subscore = round(min(100.0, att_drop), 2)
        hw_subscore = round(min(100.0, hw_drop), 2)
        test_subscore = round(min(100.0, test_drop), 2)

        # 3. Weighted Base Score
        # If any signal was never present in baseline or recent, adjust weights dynamically
        active_weights = []
        active_drops = []

        if trends.attendance_delta is not None:
            active_weights.append(ml_settings.weight_attendance)
            active_drops.append(att_drop)

        if trends.homework_delta is not None:
            active_weights.append(ml_settings.weight_homework)
            active_drops.append(hw_drop)

        if trends.test_delta is not None:
            active_weights.append(ml_settings.weight_test)
            active_drops.append(test_drop)

        if not active_weights or sum(active_weights) == 0.0:
            return RiskScoreOutput(
                risk_score=0.0,
                risk_level=RiskLevel.LOW,
                model_version=model_version,
            )

        # Normalize weights so they sum to 1.0 across available signals
        total_weight = sum(active_weights)
        weighted_base_score = sum((d * (w / total_weight)) for d, w in zip(active_drops, active_weights))

        # 4. Multipliers
        pers_mult = 1.0
        if trends.consecutive_dropping_weeks >= 2:
            pers_mult += ml_settings.persistence_multiplier

        cross_mult = 1.0
        if trends.multi_signal_decline_count >= 2:
            cross_mult += ml_settings.cross_signal_multiplier

        # Additional boost if statistical anomaly was detected
        anomaly_boost = 1.1 if anomaly.has_any_anomaly else 1.0

        # Final computed risk score clamped between 0 and 100
        final_score = weighted_base_score * pers_mult * cross_mult * anomaly_boost
        final_score = round(min(100.0, max(0.0, final_score)), 1)

        # 5. Determine Risk Level
        if final_score <= ml_settings.low_risk_max:
            level = RiskLevel.LOW
        elif final_score <= ml_settings.medium_risk_max:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.HIGH

        return RiskScoreOutput(
            risk_score=final_score,
            risk_level=level,
            model_version=model_version,
            attendance_subscore=att_subscore,
            homework_subscore=hw_subscore,
            test_subscore=test_subscore,
            applied_persistence_multiplier=round(pers_mult, 2),
            applied_cross_signal_multiplier=round(cross_mult, 2),
        )
