"""
tests/v1/test_risk_api.py — Risk Analysis API & Multi-Tenancy Tests
"""

import pytest


@pytest.fixture
def seed_class_and_declining_student():
    from tests.conftest import mock_db
    # Seed class
    mock_db.collection("classes").document("class-001").set({
        "school_id": "school-001",
        "name": "Class 10 - A",
        "grade": "10",
        "section": "A",
        "academic_year": "2024-25",
        "teacher_ids": ["teacher-uid-001"],
        "status": "ACTIVE",
    })

    # Seed student
    mock_db.collection("students").document("stu-300").set({
        "school_id": "school-001",
        "class_id": "class-001",
        "student_code": "DPS-300",
        "name": "Aman Verma",
        "grade": "10",
        "section": "A",
        "status": "ACTIVE",
    })

    # Seed subcollections across 4 weeks: Weeks 30, 31 (Baseline 100%), Weeks 32, 33 (Recent Drop to 40%)
    # Week 30 (2024-07-22 to 2024-07-26)
    mock_db.collection("students").document("stu-300").collection("attendance").document("att_w30_1").set({
        "student_id": "stu-300", "school_id": "school-001", "class_id": "class-001",
        "date": "2024-07-22", "status": "PRESENT", "source": "csv",
    })
    mock_db.collection("students").document("stu-300").collection("attendance").document("att_w30_2").set({
        "student_id": "stu-300", "school_id": "school-001", "class_id": "class-001",
        "date": "2024-07-23", "status": "PRESENT", "source": "csv",
    })

    # Week 31 (2024-07-29 to 2024-08-02)
    mock_db.collection("students").document("stu-300").collection("attendance").document("att_w31_1").set({
        "student_id": "stu-300", "school_id": "school-001", "class_id": "class-001",
        "date": "2024-07-29", "status": "PRESENT", "source": "csv",
    })

    # Week 32 (2024-08-05 to 2024-08-09) - Recent Drop
    mock_db.collection("students").document("stu-300").collection("attendance").document("att_w32_1").set({
        "student_id": "stu-300", "school_id": "school-001", "class_id": "class-001",
        "date": "2024-08-05", "status": "ABSENT", "source": "csv",
    })
    mock_db.collection("students").document("stu-300").collection("attendance").document("att_w32_2").set({
        "student_id": "stu-300", "school_id": "school-001", "class_id": "class-001",
        "date": "2024-08-06", "status": "ABSENT", "source": "csv",
    })

    # Week 33 (2024-08-12 to 2024-08-16) - Recent Drop Continued
    mock_db.collection("students").document("stu-300").collection("attendance").document("att_w33_1").set({
        "student_id": "stu-300", "school_id": "school-001", "class_id": "class-001",
        "date": "2024-08-12", "status": "ABSENT", "source": "csv",
    })


def test_analyze_student_risk_api_success(teacher_client, seed_class_and_declining_student):
    response = teacher_client.post("/api/v1/risk/analyze/student/stu-300")
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["student_id"] == "stu-300"
    assert data["risk_score"] > 30.0
    assert data["risk_level"] in ("MEDIUM", "HIGH")
    assert len(data["reasons"]) >= 1
    assert "ATTENDANCE_DECLINE" in [r["signal_type"] for r in data["reasons"]]
    assert data["alert"] is not None


def test_analyze_class_cohort_api_success(teacher_client, seed_class_and_declining_student):
    response = teacher_client.post("/api/v1/risk/analyze/class/class-001")
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["class_id"] == "class-001"
    assert data["total_students"] == 1
    assert data["high_risk_count"] + data["medium_risk_count"] >= 1
    assert len(data["alerts"]) == 1


def test_get_latest_student_alert_api(teacher_client, seed_class_and_declining_student):
    # Trigger analysis first
    teacher_client.post("/api/v1/risk/analyze/student/stu-300")

    # Query latest alert
    res = teacher_client.get("/api/v1/risk/students/stu-300/latest")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["student_id"] == "stu-300"
    assert data["status"] == "ACTIVE"
    assert len(data["reasons"]) >= 1


def test_get_student_risk_history_api(teacher_client, seed_class_and_declining_student):
    teacher_client.post("/api/v1/risk/analyze/student/stu-300")

    res = teacher_client.get("/api/v1/risk/students/stu-300/history")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) >= 1


def test_get_class_active_alerts_api(teacher_client, seed_class_and_declining_student):
    teacher_client.post("/api/v1/risk/analyze/student/stu-300")

    res = teacher_client.get("/api/v1/risk/classes/class-001/latest")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) >= 1


def test_cross_school_risk_analysis_forbidden(other_teacher_client, seed_class_and_declining_student):
    # other_teacher_client belongs to school-002; stu-300 belongs to school-001
    res = other_teacher_client.post("/api/v1/risk/analyze/student/stu-300")
    assert res.status_code == 403

    res_class = other_teacher_client.post("/api/v1/risk/analyze/class/class-001")
    assert res_class.status_code == 403
