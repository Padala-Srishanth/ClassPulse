"""
tests/v1/test_exams.py — Exam and Marks Management API Tests
"""

import pytest


def test_create_exam_success(teacher_client):
    from tests.conftest import mock_db

    mock_db.collection("classes").document("cls-exam-1").set({
        "school_id": "school-001",
        "name": "Grade 10-A",
        "grade": "10",
        "section": "A",
        "academic_year": "2024-25",
        "teacher_ids": ["teacher-uid-001"],
        "status": "ACTIVE",
    })

    payload = {
        "school_id": "school-001",
        "class_id": "cls-exam-1",
        "exam_name": "Mid-Term Mathematics",
        "subject": "Mathematics",
        "exam_date": "2024-10-15",
        "max_marks": 100.0,
    }
    res = teacher_client.post("/api/v1/exams", json=payload)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["exam_name"] == "Mid-Term Mathematics"
    assert data["max_marks"] == 100.0
    assert "id" in data


def test_enter_exam_marks_and_percentage_calculation(teacher_client):
    from tests.conftest import mock_db

    mock_db.collection("classes").document("cls-exam-2").set({
        "school_id": "school-001",
        "name": "Grade 10-B",
        "grade": "10",
        "section": "B",
        "academic_year": "2024-25",
        "teacher_ids": ["teacher-uid-001"],
        "status": "ACTIVE",
    })

    # Create exam
    payload = {
        "school_id": "school-001",
        "class_id": "cls-exam-2",
        "exam_name": "Physics Quiz",
        "subject": "Physics",
        "exam_date": "2024-10-20",
        "max_marks": 50.0,
    }
    create_res = teacher_client.post("/api/v1/exams", json=payload)
    assert create_res.status_code == 201
    exam_id = create_res.json()["data"]["id"]

    # Enter marks: 40/50 -> 80.0%, Grade A
    results_payload = {
        "results": [
            {"student_id": "stu-101", "obtained_marks": 40.0},
            {"student_id": "stu-102", "obtained_marks": 20.0},  # 20/50 -> 40.0%, Grade F
        ]
    }
    enter_res = teacher_client.post(f"/api/v1/exams/{exam_id}/results", json=results_payload)
    assert enter_res.status_code == 200
    saved = enter_res.json()["data"]["saved"]
    assert len(saved) == 2

    # Verify percentages are accurate (not multiplied twice)
    stu1 = next(r for r in saved if r["student_id"] == "stu-101")
    assert stu1["percentage"] == 80.0
    assert stu1["grade"] == "A"

    stu2 = next(r for r in saved if r["student_id"] == "stu-102")
    assert stu2["percentage"] == 40.0
    assert stu2["grade"] == "F"


def test_student_cannot_create_exam(student_client):
    payload = {
        "school_id": "school-001",
        "class_id": "cls-1",
        "exam_name": "Unauthorized Exam",
        "subject": "Math",
        "exam_date": "2024-10-15",
        "max_marks": 100.0,
    }
    res = student_client.post("/api/v1/exams", json=payload)
    assert res.status_code == 403
