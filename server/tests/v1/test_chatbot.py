"""
tests/v1/test_chatbot.py — ClassPulse AI Assistant Authorization & Behaviour Tests

Covers: teacher authorized/unauthorized queries, principal school-wide access,
cross-category filtering, individual student summaries, missing-data and
invalid-query handling, authentication failure, school isolation, role
isolation (students blocked), and multi-turn conversation.
"""

from __future__ import annotations

import pytest


def _seed_attendance(mock_db, student_id, school_id, class_id, statuses):
    for idx, (date, status) in enumerate(statuses):
        mock_db.collection("students").document(student_id).collection("attendance").document(f"att-{student_id}-{idx}").set({
            "student_id": student_id, "school_id": school_id, "class_id": class_id,
            "date": date, "status": status, "source": "csv",
        })


def _seed_homework(mock_db, student_id, school_id, class_id, statuses):
    for idx, (date, status) in enumerate(statuses):
        mock_db.collection("students").document(student_id).collection("homework").document(f"hw-{student_id}-{idx}").set({
            "student_id": student_id, "school_id": school_id, "class_id": class_id,
            "assignment_id": f"a{idx}", "assignment_date": date, "status": status, "source": "csv",
        })


def _seed_test_scores(mock_db, student_id, school_id, class_id, scores):
    for idx, (date, score) in enumerate(scores):
        mock_db.collection("students").document(student_id).collection("test_scores").document(f"ts-{student_id}-{idx}").set({
            "student_id": student_id, "school_id": school_id, "class_id": class_id,
            "subject": "Math", "assessment_name": f"Test {idx}", "assessment_date": date,
            "score": score, "max_score": 100.0, "source": "csv",
        })


def _seed_risk_alert(mock_db, student_id, school_id, class_id, risk_level, risk_score, reasons=None):
    import datetime as dt
    now = dt.datetime.now(tz=dt.timezone.utc)
    mock_db.collection("risk_alerts").document(f"alert-{student_id}").set({
        "school_id": school_id, "class_id": class_id, "student_id": student_id,
        "risk_score": risk_score, "risk_level": risk_level, "model_version": "v1-test",
        "reasons": reasons or [], "signals": {}, "analysis_period": "2024-W36",
        "status": "ACTIVE", "created_at": now, "updated_at": now,
    })


@pytest.fixture
def seed_school():
    """Two classes taught by two different teachers in the same school, plus
    one low-attendance/high-risk student and one healthy student."""
    from tests.conftest import mock_db

    mock_db.collection("classes").document("class-10a").set({
        "school_id": "school-001", "name": "Grade 10 - A", "grade": "10", "section": "A",
        "academic_year": "2024-25", "teacher_ids": ["teacher-uid-001"], "status": "ACTIVE",
    })
    mock_db.collection("classes").document("class-10b").set({
        "school_id": "school-001", "name": "Grade 10 - B", "grade": "10", "section": "B",
        "academic_year": "2024-25", "teacher_ids": ["teacher-uid-002"], "status": "ACTIVE",
    })

    mock_db.collection("students").document("stu-1").set({
        "school_id": "school-001", "class_id": "class-10a", "student_code": "STU001",
        "name": "Aman Verma", "grade": "10", "section": "A", "status": "ACTIVE",
    })
    mock_db.collection("students").document("stu-2").set({
        "school_id": "school-001", "class_id": "class-10a", "student_code": "STU002",
        "name": "Priya Sharma", "grade": "10", "section": "A", "status": "ACTIVE",
    })
    mock_db.collection("students").document("stu-3").set({
        "school_id": "school-001", "class_id": "class-10b", "student_code": "STU003",
        "name": "Ravi Kumar", "grade": "10", "section": "B", "status": "ACTIVE",
    })

    # stu-1: low attendance, declining test scores, high risk, incomplete homework
    _seed_attendance(mock_db, "stu-1", "school-001", "class-10a", [
        ("2024-08-01", "ABSENT"), ("2024-08-02", "ABSENT"), ("2024-08-03", "PRESENT"),
        ("2024-08-04", "ABSENT"), ("2024-08-05", "ABSENT"), ("2024-08-06", "ABSENT"),
        ("2024-08-07", "ABSENT"), ("2024-08-08", "ABSENT"), ("2024-08-09", "ABSENT"),
        ("2024-08-10", "ABSENT"),
    ])
    _seed_homework(mock_db, "stu-1", "school-001", "class-10a", [
        ("2024-08-01", "NOT_COMPLETED"), ("2024-08-02", "NOT_COMPLETED"), ("2024-08-03", "COMPLETED"),
    ])
    _seed_test_scores(mock_db, "stu-1", "school-001", "class-10a", [
        ("2024-07-01", 90.0), ("2024-07-08", 88.0), ("2024-08-01", 40.0), ("2024-08-08", 38.0),
    ])
    _seed_risk_alert(mock_db, "stu-1", "school-001", "class-10a", "HIGH", 82.0, reasons=[
        {"signal_type": "ATTENDANCE_DECLINE", "metric": "attendance_rate", "baseline_value": 90.0,
         "current_value": 30.0, "change": -60.0, "severity": "HIGH",
         "explanation": "Attendance dropped sharply from baseline."}
    ])

    # stu-2: healthy attendance, low risk
    _seed_attendance(mock_db, "stu-2", "school-001", "class-10a", [
        ("2024-08-01", "PRESENT"), ("2024-08-02", "PRESENT"), ("2024-08-03", "PRESENT"),
        ("2024-08-04", "PRESENT"), ("2024-08-05", "PRESENT"), ("2024-08-06", "PRESENT"),
        ("2024-08-07", "PRESENT"), ("2024-08-08", "PRESENT"), ("2024-08-09", "PRESENT"),
        ("2024-08-10", "ABSENT"),
    ])
    _seed_risk_alert(mock_db, "stu-2", "school-001", "class-10a", "LOW", 5.0)

    # stu-3 (other teacher's class): also high risk, to prove principal sees
    # school-wide data that a teacher in a different class cannot.
    _seed_attendance(mock_db, "stu-3", "school-001", "class-10b", [
        ("2024-08-01", "ABSENT"), ("2024-08-02", "ABSENT"), ("2024-08-03", "ABSENT"),
        ("2024-08-04", "PRESENT"),
    ])
    _seed_risk_alert(mock_db, "stu-3", "school-001", "class-10b", "HIGH", 75.0)

    return mock_db


# ---------------------------------------------------------------------------
# Teacher — authorized query
# ---------------------------------------------------------------------------

def test_teacher_authorized_attendance_query(teacher_client, seed_school):
    res = teacher_client.post("/api/v1/chatbot/message", json={"message": "Who has attendance below 75%?"})
    assert res.status_code == 200
    data = res.json()["data"]
    student_ids = [s["student_id"] for s in data["data"]]
    assert "stu-1" in student_ids
    assert "stu-2" not in student_ids
    assert "Aman Verma" in data["reply"]


def test_teacher_high_risk_query_scoped_to_own_class(teacher_client, seed_school):
    res = teacher_client.post("/api/v1/chatbot/message", json={"message": "Which students are currently high risk?"})
    assert res.status_code == 200
    data = res.json()["data"]
    student_ids = [s["student_id"] for s in data["data"]]
    assert "stu-1" in student_ids
    # stu-3 belongs to a different teacher's class — must never appear.
    assert "stu-3" not in student_ids


# ---------------------------------------------------------------------------
# Teacher — unauthorized (school-wide) query
# ---------------------------------------------------------------------------

def test_teacher_cannot_query_entire_school(teacher_client, seed_school):
    res = teacher_client.post("/api/v1/chatbot/message", json={"message": "Show all high-risk students in the entire school."})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["data"] is None
    assert "authorized to access" in data["reply"]


# ---------------------------------------------------------------------------
# Principal — school-wide query
# ---------------------------------------------------------------------------

def test_principal_school_wide_high_risk_query(school_admin_client, seed_school):
    res = school_admin_client.post("/api/v1/chatbot/message", json={"message": "Show all high-risk students in the school."})
    assert res.status_code == 200
    data = res.json()["data"]
    student_ids = [s["student_id"] for s in data["data"]]
    # Principal sees BOTH teachers' high-risk students.
    assert "stu-1" in student_ids
    assert "stu-3" in student_ids


# ---------------------------------------------------------------------------
# Cross-category analysis
# ---------------------------------------------------------------------------

def test_cross_category_attendance_and_declining_scores(school_admin_client, seed_school):
    res = school_admin_client.post(
        "/api/v1/chatbot/message",
        json={"message": "Show students who have attendance below 75% and declining test scores."},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    student_ids = [s["student_id"] for s in data["data"]]
    assert student_ids == ["stu-1"]


def test_cross_category_high_risk_and_low_attendance(school_admin_client, seed_school):
    res = school_admin_client.post(
        "/api/v1/chatbot/message",
        json={"message": "Show high-risk students whose attendance is below 75%."},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    student_ids = [s["student_id"] for s in data["data"]]
    assert "stu-1" in student_ids
    assert "stu-2" not in student_ids


# ---------------------------------------------------------------------------
# Individual student 360 summary
# ---------------------------------------------------------------------------

def test_individual_student_summary(school_admin_client, seed_school):
    res = school_admin_client.post(
        "/api/v1/chatbot/message",
        json={"message": 'Give me a complete summary of "Aman Verma".'},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["data"]["student"]["id"] == "stu-1"
    assert "Aman Verma" in data["reply"]
    assert data["data"]["risk_level"] == "HIGH"


def test_teacher_cannot_summarize_unauthorized_student(teacher_client, seed_school):
    res = teacher_client.post(
        "/api/v1/chatbot/message",
        json={"message": 'Give me a summary of "Ravi Kumar".'},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["data"] is None
    assert "couldn't find" in data["reply"].lower() or "authorized" in data["reply"].lower()


# ---------------------------------------------------------------------------
# Missing data
# ---------------------------------------------------------------------------

def test_missing_data_when_no_students(teacher_client):
    # No classes/students seeded for teacher-uid-001 at all in this test.
    res = teacher_client.post("/api/v1/chatbot/message", json={"message": "Who has attendance below 75%?"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["reply"] == "I couldn't find sufficient data in ClassPulse to answer that."


# ---------------------------------------------------------------------------
# Invalid / out-of-scope query
# ---------------------------------------------------------------------------

def test_out_of_scope_query(teacher_client, seed_school):
    res = teacher_client.post("/api/v1/chatbot/message", json={"message": "What's the weather like today?"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "ClassPulse" in data["reply"]


# ---------------------------------------------------------------------------
# Authentication failure
# ---------------------------------------------------------------------------

def test_authentication_failure_no_token(client):
    res = client.post("/api/v1/chatbot/message", json={"message": "Who has attendance below 75%?"})
    assert res.status_code in (401, 403)


# ---------------------------------------------------------------------------
# School isolation
# ---------------------------------------------------------------------------

def test_school_isolation_other_school_teacher_sees_nothing(other_teacher_client, seed_school):
    # mock_other_teacher_token belongs to school-002, which has no classes seeded.
    res = other_teacher_client.post("/api/v1/chatbot/message", json={"message": "Who has attendance below 75%?"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["data"] in (None, [])


# ---------------------------------------------------------------------------
# Role isolation — students blocked entirely
# ---------------------------------------------------------------------------

def test_student_blocked_from_chatbot(student_client, seed_school):
    res = student_client.post("/api/v1/chatbot/message", json={"message": "Show me my risk score."})
    assert res.status_code == 403


def test_student_blocked_from_capabilities(student_client):
    res = student_client.get("/api/v1/chatbot/capabilities")
    assert res.status_code == 403


# ---------------------------------------------------------------------------
# Multi-turn conversation
# ---------------------------------------------------------------------------

def test_multi_turn_conversation_narrows_results(school_admin_client, seed_school):
    first = school_admin_client.post("/api/v1/chatbot/message", json={"message": "Show high-risk students."})
    assert first.status_code == 200
    first_data = first.json()["data"]
    ids_first = {s["student_id"] for s in first_data["data"]}
    assert {"stu-1", "stu-3"}.issubset(ids_first)

    second = school_admin_client.post(
        "/api/v1/chatbot/message",
        json={"message": "Only Grade 10 Section A.", "context": first_data["context"]},
    )
    assert second.status_code == 200
    second_data = second.json()["data"]
    ids_second = {s["student_id"] for s in second_data["data"]}
    assert ids_second == {"stu-1"}

    third = school_admin_client.post(
        "/api/v1/chatbot/message",
        json={"message": "Which of those have attendance below 75%?", "context": second_data["context"]},
    )
    assert third.status_code == 200
    third_data = third.json()["data"]
    ids_third = {s["student_id"] for s in third_data["data"]}
    assert ids_third == {"stu-1"}


# ---------------------------------------------------------------------------
# Capabilities endpoint
# ---------------------------------------------------------------------------

def test_capabilities_for_teacher(teacher_client, seed_school):
    res = teacher_client.get("/api/v1/chatbot/capabilities")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["role"] == "TEACHER"
    assert data["is_principal"] is False
    assert data["authorized_class_count"] == 1


def test_capabilities_for_principal(school_admin_client, seed_school):
    res = school_admin_client.get("/api/v1/chatbot/capabilities")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_principal"] is True
    assert data["authorized_class_count"] == 2
