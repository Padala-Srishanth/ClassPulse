"""
tests/v1/test_monthly_analytics.py — Unit Tests for Monthly Analytics Engine
"""

import pytest
from app.analytics.aggregation import MonthlyCohortAggregator
from app.analytics.monthly_features import MonthlyFeatureExtractor
from app.analytics.monthly_risk import MonthlyBaseline, MonthlyRiskCalculator
from app.analytics.monthly_trends import MonthlyTrendAnalyzer
from app.models.academic import (
    AttendanceRecord,
    AttendanceStatus,
    HomeworkRecord,
    HomeworkStatus,
    TestScoreRecord,
)
from app.models.monthly_report import (
    DataStatus,
    MonthlyClassReport,
    MonthlyStudentReport,
    TrendDirection,
)


# ===========================================================================
# 1. Feature Extraction Tests
# ===========================================================================

def test_feature_extraction_no_data():
    features = MonthlyFeatureExtractor.extract_monthly_features(
        report_period="2026-05",
        attendance_records=[],
        homework_records=[],
        test_records=[],
    )
    assert features.data_status == DataStatus.NO_DATA
    assert features.attendance["attendance_percentage"] is None
    assert features.homework["completion_rate"] is None
    assert features.academic["average_percentage"] is None
    assert features.attendance["total_school_days"] == 0


def test_feature_extraction_sufficient_data():
    att = [
        AttendanceRecord(
            id=f"att-{i}", student_id="s1", school_id="sch1", class_id="c1",
            date=f"2026-05-{i:02d}", status=AttendanceStatus.PRESENT if i <= 8 else AttendanceStatus.LATE
        )
        for i in range(1, 11)  # 10 days: 8 present, 2 late -> (8 + 1) / 10 = 90%
    ]
    hw = [
        HomeworkRecord(
            id=f"hw-{i}", student_id="s1", school_id="sch1", class_id="c1",
            assignment_id=f"a{i}", assignment_date=f"2026-05-{i:02d}",
            status=HomeworkStatus.COMPLETED if i <= 4 else HomeworkStatus.LATE
        )
        for i in range(1, 6)  # 5 assignments: 4 completed, 1 late -> (4 + 0.5) / 5 = 90%
    ]
    tests = [
        TestScoreRecord(
            id="t1", student_id="s1", school_id="sch1", class_id="c1",
            subject="Mathematics", assessment_name="Test 1", assessment_date="2026-05-15",
            score=85.0, max_score=100.0
        ),
        TestScoreRecord(
            id="t2", student_id="s1", school_id="sch1", class_id="c1",
            subject="Science", assessment_name="Test 2", assessment_date="2026-05-20",
            score=95.0, max_score=100.0
        ),
    ]

    features = MonthlyFeatureExtractor.extract_monthly_features(
        report_period="2026-05",
        attendance_records=att,
        homework_records=hw,
        test_records=tests,
    )

    assert features.data_status == DataStatus.SUFFICIENT_DATA
    assert features.attendance["attendance_percentage"] == 90.0
    assert features.attendance["days_present"] == 8
    assert features.attendance["days_late"] == 2
    assert features.homework["completion_rate"] == 90.0
    assert features.academic["average_percentage"] == 90.0
    assert "Mathematics" in features.academic["subject_breakdown"]
    assert features.academic["subject_breakdown"]["Mathematics"]["average_percentage"] == 85.0


# ===========================================================================
# 2. Trend Analysis Tests
# ===========================================================================

def test_trend_direction_evaluation():
    # Academic improvement: 80% to 85% (+5%) -> IMPROVING
    delta, direction = MonthlyTrendAnalyzer.evaluate_metric_trend(85.0, 80.0)
    assert delta == 5.0
    assert direction == TrendDirection.IMPROVING

    # Attendance drop: 90% to 82% (-8%) -> DECLINING
    delta, direction = MonthlyTrendAnalyzer.evaluate_metric_trend(82.0, 90.0)
    assert delta == -8.0
    assert direction == TrendDirection.DECLINING

    # Stable within threshold (-2% to +2%)
    delta, direction = MonthlyTrendAnalyzer.evaluate_metric_trend(84.0, 85.0)
    assert delta == -1.0
    assert direction == TrendDirection.STABLE

    # Risk score: lower is better (risk drops from 40 to 25 -> -15 -> IMPROVING)
    delta, direction = MonthlyTrendAnalyzer.evaluate_metric_trend(25.0, 40.0, lower_is_better=True)
    assert delta == -15.0
    assert direction == TrendDirection.IMPROVING

    # Missing previous value -> INSUFFICIENT_HISTORY
    delta, direction = MonthlyTrendAnalyzer.evaluate_metric_trend(85.0, None)
    assert delta is None
    assert direction == TrendDirection.INSUFFICIENT_HISTORY


# ===========================================================================
# 3. Monthly Risk Calculation & Archetypes Tests
# ===========================================================================

def test_naturally_low_but_stable_student_is_low_risk():
    """
    Naturally low student who consistently scores ~65% has drop ~0% from baseline,
    so they should NOT be penalized as HIGH risk.
    """
    baseline = MonthlyBaseline(
        has_sufficient_history=True,
        months_observed=3,
        baseline_attendance=70.0,
        baseline_homework=65.0,
        baseline_academic=62.0,
    )
    # Current month matches baseline closely (no drop)
    risk = MonthlyRiskCalculator.evaluate_monthly_risk(
        data_status=DataStatus.SUFFICIENT_DATA,
        attendance_percentage=70.0,
        homework_completion_rate=65.0,
        academic_percentage=62.0,
        baseline=baseline,
        consecutive_declining_months=0,
    )
    assert risk.risk_score == 0.0
    assert risk.risk_level == "LOW"
    assert risk.subscores["attendance_drop"] == 0.0
    assert risk.subscores["homework_drop"] == 0.0
    assert risk.subscores["academic_drop"] == 0.0


def test_sudden_drop_student_is_high_risk():
    """
    Previously strong student whose attendance and test scores dropped dramatically
    should receive a high risk score with multi-signal multiplier.
    """
    baseline = MonthlyBaseline(
        has_sufficient_history=True,
        months_observed=3,
        baseline_attendance=96.0,
        baseline_homework=92.0,
        baseline_academic=88.0,
    )
    # Severe drop in current month across attendance, homework, and academics
    risk = MonthlyRiskCalculator.evaluate_monthly_risk(
        data_status=DataStatus.SUFFICIENT_DATA,
        attendance_percentage=45.0,   # Drop of 51%
        homework_completion_rate=50.0, # Drop of 42%
        academic_percentage=48.0,      # Drop of 40%
        baseline=baseline,
        consecutive_declining_months=2, # Triggers persistence multiplier 1.2x
    )
    assert risk.risk_score >= 50.0
    assert risk.risk_level == "HIGH"
    assert risk.multipliers["persistence"] == 1.2
    assert risk.multipliers["cross_signal"] == 1.2
    assert len(risk.risk_factors) >= 2


def test_missing_data_student_returns_no_score():
    baseline = MonthlyBaseline(has_sufficient_history=False, months_observed=0)
    risk = MonthlyRiskCalculator.evaluate_monthly_risk(
        data_status=DataStatus.NO_DATA,
        attendance_percentage=None,
        homework_completion_rate=None,
        academic_percentage=None,
        baseline=baseline,
    )
    assert risk.risk_score is None
    assert risk.risk_level == "NO_DATA"


# ===========================================================================
# 4. Cohort Aggregation Tests
# ===========================================================================

def test_class_and_school_aggregation():
    # 2 mock student reports
    s1 = MonthlyStudentReport(
        id="s1_2026-05", school_id="sch1", class_id="c1", student_id="s1", student_name="Student 1",
        report_period="2026-05", year=2026, month=5, data_status=DataStatus.SUFFICIENT_DATA,
        attendance={"attendance_percentage": 95.0},
        homework={"completion_rate": 90.0},
        academic={"average_percentage": 92.0, "subject_breakdown": {"Math": {"average_percentage": 92.0}}},
        risk={"risk_score": 5.0, "risk_level": "LOW"},
    )
    s2 = MonthlyStudentReport(
        id="s2_2026-05", school_id="sch1", class_id="c1", student_id="s2", student_name="Student 2",
        report_period="2026-05", year=2026, month=5, data_status=DataStatus.SUFFICIENT_DATA,
        attendance={"attendance_percentage": 65.0},
        homework={"completion_rate": 60.0},
        academic={"average_percentage": 58.0, "subject_breakdown": {"Math": {"average_percentage": 58.0}}},
        risk={"risk_score": 55.0, "risk_level": "HIGH", "risk_factors": ["Attendance drop"]},
    )

    class_rep = MonthlyCohortAggregator.aggregate_class_report(
        school_id="sch1", class_id="c1", class_name="10-A", grade="10", section="A",
        report_period="2026-05", student_reports=[s1, s2],
    )

    assert class_rep.total_students == 2
    assert class_rep.average_attendance == 80.0
    assert class_rep.average_homework_completion == 75.0
    assert class_rep.average_academic_percentage == 75.0
    assert class_rep.high_risk_count == 1
    assert class_rep.low_risk_count == 1

    # School aggregation
    school_rep = MonthlyCohortAggregator.aggregate_school_report(
        school_id="sch1", school_name="Demo School", report_period="2026-05",
        class_reports=[class_rep], student_reports=[s1, s2],
    )

    assert school_rep.total_students == 2
    assert school_rep.total_classes == 1
    assert school_rep.high_risk_count == 1
    assert len(school_rep.student_risk_leaderboard) == 2
    assert school_rep.student_risk_leaderboard[0]["student_id"] == "s2"
