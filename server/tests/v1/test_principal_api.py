"""
tests/v1/test_principal_api.py — Principal / School Admin API Tests
"""

import pytest


def test_principal_dashboard_success(school_admin_client):
    from tests.conftest import mock_db

    # Seed a class and student
    mock_db.collection("classes").document("cls-1").set({
        "school_id": "school-001",
        "name": "Grade 10-A",
        "grade": "10",
        "section": "A",
        "academic_year": "2024-25",
        "teacher_ids": ["teacher-uid-001"],
        "status": "ACTIVE",
    })
    mock_db.collection("students").document("stu-1").set({
        "school_id": "school-001",
        "class_id": "cls-1",
        "name": "Jane Doe",
        "student_code": "STU001",
        "grade": "10",
        "section": "A",
        "status": "ACTIVE",
    })

    res = school_admin_client.get("/api/v1/principal/dashboard")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_classes"] == 1
    assert data["total_students"] == 1
    assert "class_summaries" in data


def test_principal_dashboard_forbidden_for_teacher(teacher_client):
    res = teacher_client.get("/api/v1/principal/dashboard")
    assert res.status_code == 403


def test_principal_dashboard_forbidden_for_student(student_client):
    res = student_client.get("/api/v1/principal/dashboard")
    assert res.status_code == 403


def test_principal_class_report(school_admin_client):
    from tests.conftest import mock_db

    mock_db.collection("classes").document("cls-1").set({
        "school_id": "school-001",
        "name": "Grade 10-A",
        "grade": "10",
        "section": "A",
        "academic_year": "2024-25",
        "teacher_ids": ["teacher-uid-001"],
        "status": "ACTIVE",
    })

    res = school_admin_client.get("/api/v1/principal/classes/cls-1/report")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["class_id"] == "cls-1"
    assert "risk_distribution" in data
    assert "attendance_summary" in data


def test_principal_absentee_report(school_admin_client):
    res = school_admin_client.get("/api/v1/principal/absentees")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "report" in data
    assert "total_absentees" in data
