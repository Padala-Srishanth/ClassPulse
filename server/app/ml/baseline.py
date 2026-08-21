"""
app.ml.baseline — Student Historical Baseline Engine
"""

from __future__ import annotations

import statistics
from typing import List, Optional, Tuple
from pydantic import BaseModel

from app.ml.config import ml_settings
from app.ml.features import WeeklyEngagementSignature


class StudentBaseline(BaseModel):
    """Historical baseline metrics for a single student."""

    has_sufficient_history: bool
    total_weeks_observed: int
    baseline_weeks_count: int
    recent_weeks_count: int

    # Baseline Averages (0.0 - 100.0)
    baseline_attendance_rate: Optional[float] = None
    baseline_homework_completion_rate: Optional[float] = None
    baseline_test_average: Optional[float] = None

    # Baseline Standard Deviations (for anomaly detection)
    baseline_attendance_std: Optional[float] = None
    baseline_homework_std: Optional[float] = None
    baseline_test_std: Optional[float] = None


class BaselineCalculator:
    """Calculates student baseline and splits into baseline vs recent evaluation windows."""

    @classmethod
    def calculate_baseline(
        cls,
        signatures: List[WeeklyEngagementSignature],
        eval_window_weeks: Optional[int] = None,
    ) -> Tuple[StudentBaseline, List[WeeklyEngagementSignature], List[WeeklyEngagementSignature]]:
        """
        Split signatures into baseline window and recent evaluation window.
        Returns (baseline_object, baseline_signatures, recent_signatures).
        """
        if eval_window_weeks is None:
            eval_window_weeks = ml_settings.recent_eval_window_weeks

        total_weeks = len(signatures)

        # Insufficient history check
        if total_weeks < ml_settings.min_history_weeks:
            return (
                StudentBaseline(
                    has_sufficient_history=False,
                    total_weeks_observed=total_weeks,
                    baseline_weeks_count=0,
                    recent_weeks_count=total_weeks,
                ),
                [],
                signatures,
            )

        # Split windows:
        # If total_weeks <= eval_window_weeks + 1, use at least 1 week for baseline and remainder for eval
        if total_weeks <= eval_window_weeks:
            baseline_sigs = signatures[:1]
            recent_sigs = signatures[1:]
        else:
            baseline_sigs = signatures[:-eval_window_weeks]
            recent_sigs = signatures[-eval_window_weeks:]

        # Calculate Baseline Metrics
        att_vals = [s.attendance_rate for s in baseline_sigs if s.attendance_rate is not None]
        hw_vals = [s.homework_completion_rate for s in baseline_sigs if s.homework_completion_rate is not None]
        test_vals = [s.average_test_percentage for s in baseline_sigs if s.average_test_percentage is not None]

        # Averages
        avg_att = round(statistics.mean(att_vals), 2) if att_vals else None
        avg_hw = round(statistics.mean(hw_vals), 2) if hw_vals else None
        avg_test = round(statistics.mean(test_vals), 2) if test_vals else None

        # Standard Deviations (requires >= 2 samples)
        std_att = round(statistics.stdev(att_vals), 2) if len(att_vals) >= 2 else (0.0 if len(att_vals) == 1 else None)
        std_hw = round(statistics.stdev(hw_vals), 2) if len(hw_vals) >= 2 else (0.0 if len(hw_vals) == 1 else None)
        std_test = round(statistics.stdev(test_vals), 2) if len(test_vals) >= 2 else (0.0 if len(test_vals) == 1 else None)

        baseline = StudentBaseline(
            has_sufficient_history=True,
            total_weeks_observed=total_weeks,
            baseline_weeks_count=len(baseline_sigs),
            recent_weeks_count=len(recent_sigs),
            baseline_attendance_rate=avg_att,
            baseline_homework_completion_rate=avg_hw,
            baseline_test_average=avg_test,
            baseline_attendance_std=std_att,
            baseline_homework_std=std_hw,
            baseline_test_std=std_test,
        )

        return baseline, baseline_sigs, recent_sigs
