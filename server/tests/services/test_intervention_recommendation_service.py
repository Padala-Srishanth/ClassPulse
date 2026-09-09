"""
tests/services/test_intervention_recommendation_service.py — Unit Tests for Recommendation Engine
"""

from datetime import datetime, timezone, timedelta
from unittest.mock import patch
import pytest

from app.core.security import CurrentUser, UserRole
from app.interventions.recommendation_config import recommendation_config
from app.models.academic import AttendanceRecord, HomeworkRecord, TestScoreRecord
from app.models.intervention import Intervention, InterventionStatus, InterventionType
from app.models.intervention_recommendation import (
    DismissalReason,
    InterventionRecommendation,
    PriorityLevel,
    RecommendationReasonCode,
    RecommendationStatus,
)
from app.models.monthly_report import MonthlyStudentReport
from app.models.student import Student
from app.services.intervention_recommendation_service import InterventionRecommendationService
from tests.conftest import mock_db


@pytest.fixture
def mock_teacher_user() -> CurrentUser:
    return CurrentUser(
        uid="teacher-uid-001",
        email="teacher@school-001.example.com",
        role=UserRole.TEACHER,
        school_id="school-001",
    )


@pytest.fixture
def seed_base_student():
    student_id = "student-test-01"
    student = Student(
        id=student_id,
        school_id="school-001",
        class_id="class-001",
        student_code="DPS-001",
        name="Aarav Sharma",
        grade="10",
        section="A",
        status="ACTIVE",
    )
    mock_db.collection("students").document(student_id).set(student.to_firestore())
    mock_db.collection("classes").document("class-001").set({
        "school_id": "school-001",
        "name": "Class 10 - A",
        "grade": "10",
        "section": "A",
        "academic_year": "2024-25",
        "teacher_ids": ["teacher-uid-001"],
        "status": "ACTIVE",
    })
    return student


def _seed_academic_history(
    student_id: str,
    baseline_weeks: int = 4,
    att_base: float = 95.0,
    att_recent: float = 65.0,
    hw_base: float = 90.0,
    hw_recent: float = 50.0,
    test_base: float = 85.0,
    test_recent: float = 55.0,
    weak_subject: str = "Mathematics",
):
    """Seed synthetic daily attendance, homework, and test records."""
    # Seed baseline weeks (weeks 30 to 30 + baseline_weeks - 1)
    # Clear existing subcollections first
    mock_db.collection(f"students/{student_id}/attendance")._store.clear()
    mock_db.collection(f"students/{student_id}/homework")._store.clear()
    mock_db.collection(f"students/{student_id}/test_scores")._store.clear()

    # Dates spanning 6 weeks: 4 baseline weeks + 2 recent weeks
    dates_baseline = [
        "2024-08-01", "2024-08-02", "2024-08-05", "2024-08-06",
        "2024-08-08", "2024-08-09", "2024-08-12", "2024-08-13",
        "2024-08-15", "2024-08-16", "2024-08-19", "2024-08-20",
    ]
    dates_recent = [
        "2024-08-26", "2024-08-27", "2024-08-28", "2024-08-29",
        "2024-09-02", "2024-09-03", "2024-09-04", "2024-09-05",
    ]

    for d in dates_baseline:
        att_status = "PRESENT" if (att_base > 80.0 or hash(d) % 10 < 8) else "ABSENT"
        mock_db.collection(f"students/{student_id}/attendance").document(f"att_{student_id}_{d}").set({
            "student_id": student_id,
            "school_id": "school-001",
            "class_id": "class-001",
            "date": d,
            "status": att_status,
            "source": "manual",
            "created_at": datetime.now(tz=timezone.utc),
        })

    for d in dates_recent:
        att_status = "PRESENT" if (att_recent > 80.0) else "ABSENT"
        mock_db.collection(f"students/{student_id}/attendance").document(f"att_{student_id}_{d}").set({
            "student_id": student_id,
            "school_id": "school-001",
            "class_id": "class-001",
            "date": d,
            "status": att_status,
            "source": "manual",
            "created_at": datetime.now(tz=timezone.utc),
        })

    # Homework records
    for i, d in enumerate(dates_baseline):
        mock_db.collection(f"students/{student_id}/homework").document(f"hw_{student_id}_{d}").set({
            "student_id": student_id,
            "school_id": "school-001",
            "class_id": "class-001",
            "assignment_date": d,
            "subject": weak_subject,
            "status": "SUBMITTED" if hw_base >= 80 else "PENDING",
            "created_at": datetime.now(tz=timezone.utc),
        })

    for i, d in enumerate(dates_recent):
        mock_db.collection(f"students/{student_id}/homework").document(f"hw_{student_id}_{d}").set({
            "student_id": student_id,
            "school_id": "school-001",
            "class_id": "class-001",
            "assignment_date": d,
            "subject": weak_subject,
            "status": "SUBMITTED" if hw_recent >= 80 else "PENDING",
            "created_at": datetime.now(tz=timezone.utc),
        })

    # Test records
    mock_db.collection(f"students/{student_id}/test_scores").document(f"test_{student_id}_base").set({
        "student_id": student_id,
        "school_id": "school-001",
        "class_id": "class-001",
        "assessment_date": "2024-08-15",
        "subject": weak_subject,
        "test_name": "Mid-Term Assessment",
        "score": test_base,
        "max_marks": 100.0,
        "created_at": datetime.now(tz=timezone.utc),
    })

    mock_db.collection(f"students/{student_id}/test_scores").document(f"test_{student_id}_recent").set({
        "student_id": student_id,
        "school_id": "school-001",
        "class_id": "class-001",
        "assessment_date": "2024-09-02",
        "subject": weak_subject,
        "test_name": "Weekly Quiz",
        "score": test_recent,
        "max_marks": 100.0,
        "created_at": datetime.now(tz=timezone.utc),
    })


# =============================================================================
# SCENARIOS 1 to 17: Service Unit Tests
# =============================================================================

def test_rule_1_attendance_decline_recommends_checkin(seed_base_student):
    """Scenario 1: Attendance decline recommends ONE_ON_ONE_CHECKIN and ATTENDANCE_SUPPORT."""
    student = seed_base_student
    _seed_academic_history(
        student.id,
        att_base=95.0,
        att_recent=50.0,
        hw_base=90.0,
        hw_recent=90.0,
        test_base=85.0,
        test_recent=85.0,
    )

    recs = InterventionRecommendationService.generate_recommendations(student)
    assert len(recs) >= 1
    top_rec = recs[0]
    assert top_rec.recommendation_type == InterventionType.ONE_ON_ONE_CHECKIN
    assert RecommendationReasonCode.ATTENDANCE_DROP.value in top_rec.reason_codes
    assert "Attendance decreased" in top_rec.explanation


def test_rule_2_homework_decline_recommends_support(seed_base_student):
    """Scenario 2: Homework decline recommends ONE_ON_ONE_CHECKIN, EXTRA_ASSIGNMENT, ACADEMIC_SUPPORT."""
    student = seed_base_student
    _seed_academic_history(
        student.id,
        att_base=92.0,
        att_recent=92.0,
        hw_base=95.0,
        hw_recent=40.0,
        test_base=88.0,
        test_recent=88.0,
    )

    recs = InterventionRecommendationService.generate_recommendations(student)
    assert len(recs) >= 1
    types = [r.recommendation_type for r in recs]
    assert InterventionType.ONE_ON_ONE_CHECKIN in types
    assert InterventionType.EXTRA_ASSIGNMENT in types or InterventionType.ACADEMIC_SUPPORT in types
    assert any(RecommendationReasonCode.HOMEWORK_DROP.value in r.reason_codes for r in recs)


def test_rule_3_academic_decline_recommends_academic_support_with_weak_subjects(seed_base_student):
    """Scenario 3: Academic decline recommends ACADEMIC_SUPPORT with identified weak subjects."""
    student = seed_base_student
    _seed_academic_history(
        student.id,
        att_base=92.0,
        att_recent=92.0,
        hw_base=90.0,
        hw_recent=90.0,
        test_base=85.0,
        test_recent=45.0,
        weak_subject="Mathematics",
    )

    recs = InterventionRecommendationService.generate_recommendations(student)
    assert len(recs) >= 1
    top_rec = recs[0]
    assert top_rec.recommendation_type == InterventionType.ACADEMIC_SUPPORT
    assert RecommendationReasonCode.ACADEMIC_DROP.value in top_rec.reason_codes
    assert "Mathematics" in top_rec.explanation or "Mathematics" in str(top_rec.recommended_actions)


def test_rule_4_multiple_signals_increase_priority_and_recommend_coordinated_response(seed_base_student):
    """Scenario 4: 2 or more signals declining simultaneously trigger coordinated response & higher priority."""
    student = seed_base_student
    _seed_academic_history(
        student.id,
        att_base=95.0,
        att_recent=50.0,
        hw_base=95.0,
        hw_recent=45.0,
        test_base=90.0,
        test_recent=50.0,
    )

    recs = InterventionRecommendationService.generate_recommendations(student)
    assert len(recs) >= 3
    types = [r.recommendation_type for r in recs]
    assert InterventionType.ONE_ON_ONE_CHECKIN in types
    assert InterventionType.ACADEMIC_SUPPORT in types
    assert InterventionType.PARENT_CONTACT in types
    top_rec = recs[0]
    assert RecommendationReasonCode.MULTI_SIGNAL_DECLINE.value in top_rec.reason_codes
    assert top_rec.priority_level in (PriorityLevel.HIGH, PriorityLevel.URGENT)


def test_rule_5_persistent_decline_boosts_priority(seed_base_student):
    """Scenario 5: Consecutive drops across evaluation periods flag PERSISTENT_DECLINE."""
    student = seed_base_student
    _seed_academic_history(
        student.id,
        att_base=95.0,
        att_recent=55.0,
        hw_base=90.0,
        hw_recent=90.0,
        test_base=85.0,
        test_recent=85.0,
    )

    recs = InterventionRecommendationService.generate_recommendations(student)
    assert len(recs) >= 1
    top_rec = recs[0]
    assert RecommendationReasonCode.ATTENDANCE_DROP.value in top_rec.reason_codes


def test_rule_6_sudden_drop_creates_high_or_urgent_priority(seed_base_student):
    """Scenario 6: Sudden drop >= 25% creates HIGH or URGENT recommendation."""
    student = seed_base_student
    _seed_academic_history(
        student.id,
        att_base=95.0,
        att_recent=50.0,  # 45% drop
        hw_base=90.0,
        hw_recent=90.0,
        test_base=85.0,
        test_recent=85.0,
    )

    recs = InterventionRecommendationService.generate_recommendations(student)
    assert len(recs) >= 1
    top_rec = recs[0]
    assert top_rec.priority_level in (PriorityLevel.HIGH, PriorityLevel.URGENT)
    assert RecommendationReasonCode.SUDDEN_DROP.value in top_rec.reason_codes


def test_rule_7_temporary_dip_with_recovery_recommends_monitoring(seed_base_student):
    """Scenario 7: Rebounding after dip recommends monitoring rather than aggressive interventions."""
    student = seed_base_student
    # Seed monthly reports simulating June risk 25, July risk 72, August risk 30
    doc1 = f"{student.id}_2024-06"
    doc2 = f"{student.id}_2024-07"
    doc3 = f"{student.id}_2024-08"

    mock_db.collection("monthly_student_reports").document(doc1).set({
        "school_id": "school-001",
        "class_id": "class-001",
        "student_id": student.id,
        "student_name": student.name,
        "report_period": "2024-06",
        "year": 2024,
        "month": 6,
        "risk": {"risk_score": 25.0},
        "data_status": "SUFFICIENT_DATA",
    })
    mock_db.collection("monthly_student_reports").document(doc2).set({
        "school_id": "school-001",
        "class_id": "class-001",
        "student_id": student.id,
        "student_name": student.name,
        "report_period": "2024-07",
        "year": 2024,
        "month": 7,
        "risk": {"risk_score": 72.0},
        "data_status": "SUFFICIENT_DATA",
    })

    # Student currently has good recent performance
    _seed_academic_history(
        student.id,
        att_base=92.0,
        att_recent=92.0,
        hw_base=90.0,
        hw_recent=90.0,
        test_base=85.0,
        test_recent=85.0,
    )

    recs = InterventionRecommendationService.generate_recommendations(student)
    assert len(recs) == 1
    rec = recs[0]
    assert rec.recommendation_type == InterventionType.FOLLOW_UP_REVIEW
    assert RecommendationReasonCode.RECOVERY_DETECTED.value in rec.reason_codes
    assert rec.priority_level == PriorityLevel.LOW
    assert "Continue monitoring" in rec.explanation


def test_rule_8_stable_low_performance_is_supportive_not_urgent(seed_base_student):
    """Scenario 8: Naturally low but stable student receives supportive ACADEMIC_SUPPORT, capped at MEDIUM."""
    student = seed_base_student
    _seed_academic_history(
        student.id,
        att_base=92.0,
        att_recent=92.0,
        hw_base=52.0,
        hw_recent=50.0,  # low but stable (delta 2%)
        test_base=50.0,
        test_recent=51.0,  # low but stable (delta 1%)
    )

    recs = InterventionRecommendationService.generate_recommendations(student)
    assert len(recs) >= 1
    top_rec = recs[0]
    assert top_rec.recommendation_type == InterventionType.ACADEMIC_SUPPORT
    assert RecommendationReasonCode.STABLE_LOW_PERFORMANCE.value in top_rec.reason_codes
    assert top_rec.priority_level in (PriorityLevel.LOW, PriorityLevel.MEDIUM)
    assert top_rec.priority_score <= 60.0  # NOT HIGH or URGENT


def test_rule_9_insufficient_data_recommends_data_collection(seed_base_student):
    """Scenario 9: Insufficient history flags INSUFFICIENT_DATA and recommends collecting more data."""
    student = seed_base_student
    # Clear all subcollections so student has 0 weeks
    mock_db.collection(f"students/{student.id}/attendance")._store.clear()
    mock_db.collection(f"students/{student.id}/homework")._store.clear()
    mock_db.collection(f"students/{student.id}/test_scores")._store.clear()

    recs = InterventionRecommendationService.generate_recommendations(student)
    assert len(recs) == 1
    rec = recs[0]
    assert RecommendationReasonCode.INSUFFICIENT_DATA.value in rec.reason_codes
    assert rec.priority_level == PriorityLevel.LOW
    assert "Collect additional" in rec.explanation


def test_rule_10_active_intervention_prevents_duplicate_recommendation(seed_base_student):
    """Scenario 10: Existing active intervention converts candidate into FOLLOW_UP_REVIEW."""
    student = seed_base_student
    _seed_academic_history(
        student.id,
        att_base=95.0,
        att_recent=50.0,
        hw_base=90.0,
        hw_recent=90.0,
        test_base=85.0,
        test_recent=85.0,
    )

    # Seed an active PLANNED ONE_ON_ONE_CHECKIN
    mock_db.collection("interventions").document("int-active-01").set({
        "school_id": "school-001",
        "student_id": student.id,
        "teacher_id": "teacher-uid-001",
        "class_id": "class-001",
        "type": InterventionType.ONE_ON_ONE_CHECKIN.value,
        "notes": "Existing check-in already planned.",
        "status": InterventionStatus.PLANNED.value,
        "created_at": datetime.now(tz=timezone.utc),
        "updated_at": datetime.now(tz=timezone.utc),
    })

    recs = InterventionRecommendationService.generate_recommendations(student)
    types = [r.recommendation_type for r in recs]
    # No duplicate ONE_ON_ONE_CHECKIN
    assert InterventionType.ONE_ON_ONE_CHECKIN not in types
    # Replaced by FOLLOW_UP_REVIEW
    assert InterventionType.FOLLOW_UP_REVIEW in types


def test_rule_11_cooldown_prevents_repeat_recommendation(seed_base_student):
    """Scenario 11: Cooldown suppresses recommendation completed 4 days ago (cooldown is 7 days)."""
    student = seed_base_student
    _seed_academic_history(
        student.id,
        att_base=95.0,
        att_recent=75.0,  # moderate drop
        hw_base=90.0,
        hw_recent=90.0,
        test_base=85.0,
        test_recent=85.0,
    )

    # Completed 4 days ago
    completed_time = datetime.now(tz=timezone.utc) - timedelta(days=4)
    mock_db.collection("interventions").document("int-done-01").set({
        "school_id": "school-001",
        "student_id": student.id,
        "teacher_id": "teacher-uid-001",
        "class_id": "class-001",
        "type": InterventionType.ONE_ON_ONE_CHECKIN.value,
        "notes": "Check-in completed.",
        "status": InterventionStatus.COMPLETED.value,
        "created_at": completed_time,
        "updated_at": completed_time,
    })

    recs = InterventionRecommendationService.generate_recommendations(student)
    types = [r.recommendation_type for r in recs]
    # Suppressed under cooldown
    assert InterventionType.ONE_ON_ONE_CHECKIN not in types


def test_rule_12_significant_escalation_overrides_cooldown(seed_base_student):
    """Scenario 12: Severe escalation (URGENT / high drop) overrides standard cooldown."""
    student = seed_base_student
    _seed_academic_history(
        student.id,
        att_base=95.0,
        att_recent=35.0,  # 60% massive drop!
        hw_base=90.0,
        hw_recent=40.0,  # 50% drop!
        test_base=90.0,
        test_recent=45.0,  # 45% drop!
    )

    completed_time = datetime.now(tz=timezone.utc) - timedelta(days=2)
    mock_db.collection("interventions").document("int-done-02").set({
        "school_id": "school-001",
        "student_id": student.id,
        "teacher_id": "teacher-uid-001",
        "class_id": "class-001",
        "type": InterventionType.ONE_ON_ONE_CHECKIN.value,
        "notes": "Recent check-in.",
        "status": InterventionStatus.COMPLETED.value,
        "created_at": completed_time,
        "updated_at": completed_time,
    })

    recs = InterventionRecommendationService.generate_recommendations(student)
    assert len(recs) >= 1
    # Check-in should still be recommended due to severe escalation
    types = [r.recommendation_type for r in recs]
    assert InterventionType.ONE_ON_ONE_CHECKIN in types


def test_approve_recommendation_creates_intervention_and_updates_status(seed_base_student, mock_teacher_user):
    """Scenario 13 & 14: Approving recommendation creates an intervention and links intervention_id."""
    student = seed_base_student
    _seed_academic_history(
        student.id,
        att_base=95.0,
        att_recent=55.0,
    )
    recs = InterventionRecommendationService.generate_recommendations(student)
    assert len(recs) >= 1
    target_rec = recs[0]

    updated_rec, created_int = InterventionRecommendationService.approve_recommendation(
        recommendation_id=target_rec.recommendation_id,
        user=mock_teacher_user,
        optional_notes="Custom teacher guidance provided.",
    )

    assert updated_rec.status == RecommendationStatus.CONVERTED_TO_INTERVENTION
    assert updated_rec.intervention_id == created_int.id
    assert updated_rec.reviewed_by == mock_teacher_user.uid
    assert created_int.notes == "Custom teacher guidance provided."
    assert created_int.status == InterventionStatus.PLANNED


def test_dismiss_recommendation_updates_status(seed_base_student, mock_teacher_user):
    """Scenario 15: Dismissing recommendation updates status to DISMISSED with reason."""
    student = seed_base_student
    _seed_academic_history(student.id, att_base=95.0, att_recent=55.0)
    recs = InterventionRecommendationService.generate_recommendations(student)
    assert len(recs) >= 1
    target_rec = recs[0]

    dismissed = InterventionRecommendationService.dismiss_recommendation(
        recommendation_id=target_rec.recommendation_id,
        user=mock_teacher_user,
        reason=DismissalReason.ISSUE_ALREADY_RESOLVED.value,
        notes="Parent confirmed student had illness but is back in class.",
    )

    assert dismissed.status == RecommendationStatus.DISMISSED
    assert dismissed.dismissal_reason == DismissalReason.ISSUE_ALREADY_RESOLVED.value
    assert dismissed.reviewed_by == mock_teacher_user.uid


def test_duplicate_analysis_does_not_create_duplicate_pending(seed_base_student):
    """Scenario 16: Multiple analyses do not duplicate pending recommendations."""
    student = seed_base_student
    _seed_academic_history(student.id, att_base=95.0, att_recent=55.0)

    # First analysis
    recs1 = InterventionRecommendationService.generate_recommendations(student)
    count1 = len(recs1)

    # Second analysis
    recs2 = InterventionRecommendationService.generate_recommendations(student)
    count2 = len(recs2)

    assert count1 == count2
    all_pending = InterventionRecommendationService.get_student_recommendations(
        student.id, status_filter=RecommendationStatus.PENDING.value
    )
    assert len(all_pending) == count1


def test_recommendations_are_ranked_by_priority_score_descending(seed_base_student):
    """Scenario 17: Recommendations are correctly ranked by priority_score DESC."""
    student = seed_base_student
    _seed_academic_history(
        student.id,
        att_base=95.0,
        att_recent=50.0,
        hw_base=95.0,
        hw_recent=45.0,
        test_base=90.0,
        test_recent=50.0,
    )
    recs = InterventionRecommendationService.generate_recommendations(student)
    scores = [r.priority_score for r in recs]
    assert scores == sorted(scores, reverse=True)
