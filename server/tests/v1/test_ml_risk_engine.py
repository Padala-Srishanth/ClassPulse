"""
tests/v1/test_ml_risk_engine.py — Synthetic Cohort Validation & ML Engine Tests
"""

import pytest

from app.ml.anomaly import AnomalyDetector
from app.ml.baseline import BaselineCalculator
from app.ml.explainability import ExplainabilityEngine
from app.ml.features import WeeklyEngagementSignature
from app.ml.scoring import RiskLevel, RiskScorer
from app.ml.trends import TrendAnalyzer


def _run_pipeline(signatures):
    baseline, baseline_sigs, recent_sigs = BaselineCalculator.calculate_baseline(signatures)
    trends = TrendAnalyzer.analyze_trends(baseline, recent_sigs)
    anomaly = AnomalyDetector.detect_anomalies(baseline, trends)
    score_output = RiskScorer.compute_risk(baseline, trends, anomaly)
    reasons = ExplainabilityEngine.generate_reasons(baseline, trends, anomaly, score_output)
    return baseline, trends, anomaly, score_output, reasons


# ---------------------------------------------------------------------------
# Synthetic Benchmark Cohort
# ---------------------------------------------------------------------------

def test_student_a_stable_high_achiever():
    """Student A has consistently high attendance (95%), homework (95%), test (90%). Should be LOW risk."""
    sigs = [
        WeeklyEngagementSignature(week_key=f"2024-W{i:02d}", attendance_rate=95.0, homework_completion_rate=95.0, average_test_percentage=90.0)
        for i in range(30, 36)  # 6 weeks
    ]
    _, _, _, score_output, reasons = _run_pipeline(sigs)
    assert score_output.risk_level == RiskLevel.LOW
    assert score_output.risk_score <= 10.0
    assert any(r.signal_type == "STABLE_PERFORMANCE" for r in reasons)


def test_student_b_improving_student():
    """Student B had moderate past baseline (75%) but recent weeks improved (90%). Should be LOW risk."""
    sigs = [
        WeeklyEngagementSignature(week_key="2024-W30", attendance_rate=75.0, homework_completion_rate=70.0, average_test_percentage=65.0),
        WeeklyEngagementSignature(week_key="2024-W31", attendance_rate=75.0, homework_completion_rate=72.0, average_test_percentage=68.0),
        WeeklyEngagementSignature(week_key="2024-W32", attendance_rate=80.0, homework_completion_rate=78.0, average_test_percentage=72.0),
        WeeklyEngagementSignature(week_key="2024-W33", attendance_rate=88.0, homework_completion_rate=85.0, average_test_percentage=80.0),
        WeeklyEngagementSignature(week_key="2024-W34", attendance_rate=92.0, homework_completion_rate=90.0, average_test_percentage=85.0),
    ]
    _, trends, _, score_output, _ = _run_pipeline(sigs)
    assert score_output.risk_level == RiskLevel.LOW
    assert score_output.risk_score == 0.0
    assert trends.attendance_delta > 0  # positive improvement


def test_student_c_gradual_decline():
    """Student C had high baseline (95%), but dropped across multiple consecutive weeks (85% -> 70% -> 60%)."""
    sigs = [
        WeeklyEngagementSignature(week_key="2024-W30", attendance_rate=96.0, homework_completion_rate=95.0, average_test_percentage=92.0),
        WeeklyEngagementSignature(week_key="2024-W31", attendance_rate=94.0, homework_completion_rate=93.0, average_test_percentage=90.0),
        WeeklyEngagementSignature(week_key="2024-W32", attendance_rate=95.0, homework_completion_rate=94.0, average_test_percentage=89.0),
        WeeklyEngagementSignature(week_key="2024-W33", attendance_rate=80.0, homework_completion_rate=75.0, average_test_percentage=72.0),
        WeeklyEngagementSignature(week_key="2024-W34", attendance_rate=65.0, homework_completion_rate=60.0, average_test_percentage=62.0),
    ]
    _, trends, _, score_output, reasons = _run_pipeline(sigs)
    assert score_output.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
    assert score_output.risk_score >= 30.0
    # Must contain persistent decline or multi-signal reason

    reason_types = [r.signal_type for r in reasons]
    assert "ATTENDANCE_DECLINE" in reason_types
    assert "HOMEWORK_DECLINE" in reason_types
    assert "TEST_SCORE_DECLINE" in reason_types


def test_student_d_sudden_sharp_drop():
    """Student D experiences an abrupt collapse across attendance (95% -> 50%) and homework (95% -> 30%)."""
    sigs = [
        WeeklyEngagementSignature(week_key="2024-W30", attendance_rate=98.0, homework_completion_rate=95.0, average_test_percentage=90.0),
        WeeklyEngagementSignature(week_key="2024-W31", attendance_rate=95.0, homework_completion_rate=92.0, average_test_percentage=88.0),
        WeeklyEngagementSignature(week_key="2024-W32", attendance_rate=96.0, homework_completion_rate=94.0, average_test_percentage=91.0),
        WeeklyEngagementSignature(week_key="2024-W33", attendance_rate=50.0, homework_completion_rate=30.0, average_test_percentage=55.0),
        WeeklyEngagementSignature(week_key="2024-W34", attendance_rate=45.0, homework_completion_rate=25.0, average_test_percentage=50.0),
    ]
    _, _, anomaly, score_output, reasons = _run_pipeline(sigs)
    assert score_output.risk_level == RiskLevel.HIGH
    assert score_output.risk_score >= 60.0
    assert anomaly.has_any_anomaly is True
    reason_types = [r.signal_type for r in reasons]
    assert "MULTI_SIGNAL_AGREEMENT" in reason_types


def test_student_e_insufficient_data():
    """Student E only has 1 week of data. Must flag INSUFFICIENT_DATA and NOT generate a false high risk."""
    sigs = [
        WeeklyEngagementSignature(week_key="2024-W30", attendance_rate=50.0, homework_completion_rate=40.0),
    ]
    _, _, _, score_output, reasons = _run_pipeline(sigs)
    assert score_output.risk_level == RiskLevel.INSUFFICIENT_DATA
    assert score_output.risk_score == 0.0
    assert reasons[0].signal_type == "INSUFFICIENT_HISTORY"


def test_student_f_naturally_low_but_stable():
    """
    CRITICAL TEST: Student F is consistently at 65% attendance and 60% homework every week.
    Because there is NO deviation from their historical baseline, they should NOT be flagged as declining!
    """
    sigs = [
        WeeklyEngagementSignature(week_key=f"2024-W{i:02d}", attendance_rate=65.0, homework_completion_rate=60.0, average_test_percentage=58.0)
        for i in range(30, 36)
    ]
    _, trends, _, score_output, _ = _run_pipeline(sigs)
    assert score_output.risk_level == RiskLevel.LOW
    assert score_output.risk_score == 0.0
    assert abs(trends.attendance_delta) < 1.0


def test_student_g_temporary_dip_and_recovery():
    """Student G had a slight dip in week 33 (85%) but was 95% before and 92% in week 34. Should remain LOW risk."""
    sigs = [
        WeeklyEngagementSignature(week_key="2024-W30", attendance_rate=95.0, homework_completion_rate=95.0),
        WeeklyEngagementSignature(week_key="2024-W31", attendance_rate=95.0, homework_completion_rate=95.0),
        WeeklyEngagementSignature(week_key="2024-W32", attendance_rate=95.0, homework_completion_rate=95.0),
        WeeklyEngagementSignature(week_key="2024-W33", attendance_rate=85.0, homework_completion_rate=85.0),
        WeeklyEngagementSignature(week_key="2024-W34", attendance_rate=92.0, homework_completion_rate=92.0),
    ]
    _, _, _, score_output, _ = _run_pipeline(sigs)
    assert score_output.risk_level == RiskLevel.LOW
    assert score_output.risk_score <= 20.0
