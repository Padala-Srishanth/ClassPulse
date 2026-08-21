"""
app.ml.trends — Trend Analysis & Trajectory Evaluation
"""

from __future__ import annotations

import statistics
from typing import List, Optional
from pydantic import BaseModel

from app.ml.baseline import StudentBaseline
from app.ml.config import ml_settings
from app.ml.features import WeeklyEngagementSignature


class TrendSummary(BaseModel):
    """Summarized trends and deviations between baseline and recent evaluation window."""

    # Recent window averages
    recent_attendance_rate: Optional[float] = None
    recent_homework_completion_rate: Optional[float] = None
    recent_test_average: Optional[float] = None

    # Deltas (recent - baseline). Negative value means decline.
    attendance_delta: Optional[float] = None
    homework_delta: Optional[float] = None
    test_delta: Optional[float] = None

    # Significant drop boolean flags
    is_attendance_declining: bool = False
    is_homework_declining: bool = False
    is_test_declining: bool = False

    # Persistence of decline (consecutive dropping weeks in recent window)
    consecutive_dropping_weeks: int = 0
    multi_signal_decline_count: int = 0


class TrendAnalyzer:
    """Evaluates recent trends against the student's historical baseline."""

    @classmethod
    def analyze_trends(
        cls,
        baseline: StudentBaseline,
        recent_signatures: List[WeeklyEngagementSignature],
    ) -> TrendSummary:
        if not baseline.has_sufficient_history or not recent_signatures:
            return TrendSummary()

        # Extract recent values
        recent_att_vals = [s.attendance_rate for s in recent_signatures if s.attendance_rate is not None]
        recent_hw_vals = [s.homework_completion_rate for s in recent_signatures if s.homework_completion_rate is not None]
        recent_test_vals = [s.average_test_percentage for s in recent_signatures if s.average_test_percentage is not None]

        recent_att = round(statistics.mean(recent_att_vals), 2) if recent_att_vals else None
        recent_hw = round(statistics.mean(recent_hw_vals), 2) if recent_hw_vals else None
        recent_test = round(statistics.mean(recent_test_vals), 2) if recent_test_vals else None

        # Compute Deltas (recent - baseline)
        att_delta = round(recent_att - baseline.baseline_attendance_rate, 2) if (recent_att is not None and baseline.baseline_attendance_rate is not None) else None
        hw_delta = round(recent_hw - baseline.baseline_homework_completion_rate, 2) if (recent_hw is not None and baseline.baseline_homework_completion_rate is not None) else None
        test_delta = round(recent_test - baseline.baseline_test_average, 2) if (recent_test is not None and baseline.baseline_test_average is not None) else None

        # Detect Significant Declines (drop >= threshold)
        is_att_drop = att_delta is not None and att_delta <= -ml_settings.significant_drop_attendance
        is_hw_drop = hw_delta is not None and hw_delta <= -ml_settings.significant_drop_homework
        is_test_drop = test_delta is not None and test_delta <= -ml_settings.significant_drop_test

        declining_signals_count = sum([1 for flag in (is_att_drop, is_hw_drop, is_test_drop) if flag])

        # Calculate consecutive declining weeks across the signature sequence
        consecutive_drops = 0
        if len(recent_signatures) >= 2:
            # Check if each week in recent window had lower attendance or homework than previous
            dropping_sequence = True
            for i in range(1, len(recent_signatures)):
                curr_att = recent_signatures[i].attendance_rate
                prev_att = recent_signatures[i - 1].attendance_rate
                curr_hw = recent_signatures[i].homework_completion_rate
                prev_hw = recent_signatures[i - 1].homework_completion_rate

                att_dropped = (curr_att is not None and prev_att is not None and curr_att < prev_att)
                hw_dropped = (curr_hw is not None and prev_hw is not None and curr_hw < prev_hw)

                if att_dropped or hw_dropped:
                    consecutive_drops += 1
                else:
                    dropping_sequence = False

            if not dropping_sequence:
                consecutive_drops = 0

        return TrendSummary(
            recent_attendance_rate=recent_att,
            recent_homework_completion_rate=recent_hw,
            recent_test_average=recent_test,
            attendance_delta=att_delta,
            homework_delta=hw_delta,
            test_delta=test_delta,
            is_attendance_declining=is_att_drop,
            is_homework_declining=is_hw_drop,
            is_test_declining=is_test_drop,
            consecutive_dropping_weeks=consecutive_drops,
            multi_signal_decline_count=declining_signals_count,
        )
