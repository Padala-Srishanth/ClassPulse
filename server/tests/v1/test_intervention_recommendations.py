"""
tests/v1/test_intervention_recommendations.py — API Integration & RBAC Tests
"""

from datetime import datetime, timezone
import pytest

from app.models.intervention import InterventionType
from app.models.intervention_recommendation import (
    DismissalReason,
    InterventionRecommendation,
    PriorityLevel,
    RecommendationStatus,
)
from tests.conftest import mock_db


@pytest.fixture
def seed_cohort_for_recommendations():
    # School 1 Student & Class
    mock_db.collection("students").document("stu-rec-001").set({
        "school_id": "school-001",
        "class_id": "class-rec-001",
        "student_code": "DPS-REC-01",
        "name": "Rohan Gupta",
        "grade": "10",
        "section": "A",
        "status": "ACTIVE",
    })
    mock_db.collection("classes").document("class-rec-001").set({
        "school_id": "school-001",
        "name": "Class 10 - A",
        "grade": "10",
        "section": "A",
        "status": "ACTIVE",
    })

    # School 2 Student & Class (for cross-school testing)
    mock_db.collection("students").document("stu-rec-002").set({
        "school_id": "school-002",
        "class_id": "class-rec-002",
        "student_code": "DPS-REC-02",
        "name": "Ananya Sen",
        "grade": "10",
        "section": "B",
        "status": "ACTIVE",
    })
    mock_db.collection("classes").document("class-rec-002").set({
        "school_id": "school-002",
        "name": "Class 10 - B",
        "grade": "10",
        "section": "B",
        "status": "ACTIVE",
    })

    # Pre-seed a recommendation in Firestore
    now = datetime.now(tz=timezone.utc)
    rec1 = InterventionRecommendation(
        recommendation_id="rec_stu-rec-001_2024-W36_ONE_ON_ONE_CHECKIN",
        school_id="school-001",
        student_id="stu-rec-001",
        student_name="Rohan Gupta",
        class_id="class-rec-001",
        class_name="Class 10 - A",
        report_period="2024-W36",
        recommendation_type=InterventionType.ONE_ON_ONE_CHECKIN,
        priority_level=PriorityLevel.HIGH,
        priority_score=75.0,
        status=RecommendationStatus.PENDING,
        reason_codes=["ATTENDANCE_DROP"],
        explanation="Attendance decreased from 92% to 65%.",
        recommended_actions=["Meet student privately."],
        suggested_follow_up_days=7,
        created_at=now,
        updated_at=now,
    )
    mock_db.collection("intervention_recommendations").document(rec1.recommendation_id).set(rec1.to_firestore())


def test_analyze_student_endpoint_success(teacher_client, seed_cohort_for_recommendations):
    """POST /student/{id}/analyze creates/returns recommendations."""
    res = teacher_client.post("/api/v1/intervention-recommendations/student/stu-rec-001/analyze")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    assert isinstance(json_data["data"], list)


def test_get_student_recommendations_endpoint(teacher_client, seed_cohort_for_recommendations):
    """GET /student/{id} retrieves recommendations."""
    res = teacher_client.get("/api/v1/intervention-recommendations/student/stu-rec-001")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert len(data) >= 1
    assert data[0]["student_id"] == "stu-rec-001"


def test_get_class_pending_recommendations_endpoint(teacher_client, seed_cohort_for_recommendations):
    """Scenario 18: Teacher sees authorized class recommendations."""
    res = teacher_client.get("/api/v1/intervention-recommendations/class/class-rec-001")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert len(data) >= 1
    assert data[0]["class_id"] == "class-rec-001"


def test_get_school_recommendations_principal(school_admin_client, seed_cohort_for_recommendations):
    """Scenario 19: Principal sees only their school's recommendations."""
    res = school_admin_client.get("/api/v1/intervention-recommendations/school/school-001")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert all(r["school_id"] == "school-001" for r in data)


def test_cross_school_access_returns_403(other_teacher_client, seed_cohort_for_recommendations):
    """Scenario 20: Cross-school access returns 403 Forbidden."""
    # other_teacher_client belongs to school-002, attempting to access school-001 student
    res = other_teacher_client.get("/api/v1/intervention-recommendations/student/stu-rec-001")
    assert res.status_code == 403


def test_student_cannot_access_recommendations(student_client, seed_cohort_for_recommendations):
    """Scenario 21: Student role is forbidden from viewing internal teacher recommendations."""
    # Student accessing own student recommendations
    res = student_client.get("/api/v1/intervention-recommendations/student/stu-rec-001")
    assert res.status_code == 403


def test_approve_recommendation_endpoint(teacher_client, seed_cohort_for_recommendations):
    """POST /{id}/approve converts recommendation into real intervention."""
    rec_id = "rec_stu-rec-001_2024-W36_ONE_ON_ONE_CHECKIN"
    payload = {
        "notes": "Discussed attendance target with Rohan.",
        "follow_up_date": "2024-09-25",
    }
    res = teacher_client.post(f"/api/v1/intervention-recommendations/{rec_id}/approve", json=payload)
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert data["recommendation"]["status"] == "CONVERTED_TO_INTERVENTION"
    assert "intervention_id" in data
    assert data["intervention_id"] is not None


def test_dismiss_recommendation_endpoint(teacher_client, seed_cohort_for_recommendations):
    """POST /{id}/dismiss updates recommendation status to DISMISSED."""
    rec_id = "rec_stu-rec-001_2024-W36_ONE_ON_ONE_CHECKIN"
    payload = {
        "reason": DismissalReason.ISSUE_ALREADY_RESOLVED.value,
        "notes": "Spoke to student, medical leave was already approved.",
    }
    res = teacher_client.post(f"/api/v1/intervention-recommendations/{rec_id}/dismiss", json=payload)
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert data["status"] == "DISMISSED"
    assert data["dismissal_reason"] == DismissalReason.ISSUE_ALREADY_RESOLVED.value
