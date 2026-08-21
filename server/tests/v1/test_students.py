"""
tests/v1/test_students.py — Student API Tests
"""

import pytest


def test_create_student(school_admin_client):
    payload = {
        "school_id": "school-001",
        "class_id": "class-001",
        "student_code": "DPS-101",
        "name": "Rahul Kumar",
        "grade": "10",
        "section": "A",
    }
    response = school_admin_client.post("/api/v1/students", json=payload)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "Rahul Kumar"
    assert data["student_code"] == "DPS-101"


def test_create_student_duplicate_code_rejected(school_admin_client):
    from tests.conftest import mock_db
    mock_db.collection("students").document("stu-1").set({
        "school_id": "school-001",
        "class_id": "class-001",
        "student_code": "DPS-101",
        "name": "Existing Student",
        "grade": "10",
        "section": "A",
        "status": "ACTIVE",
    })

    payload = {
        "school_id": "school-001",
        "class_id": "class-001",
        "student_code": "DPS-101",
        "name": "New Student Same Code",
        "grade": "10",
        "section": "A",
    }
    response = school_admin_client.post("/api/v1/students", json=payload)
    assert response.status_code == 409


def test_get_student_details(teacher_client):
    from tests.conftest import mock_db
    mock_db.collection("students").document("stu-10").set({
        "school_id": "school-001",
        "class_id": "class-001",
        "student_code": "DPS-102",
        "name": "Sneha Sharma",
        "grade": "10",
        "section": "A",
        "status": "ACTIVE",
    })

    res = teacher_client.get("/api/v1/students/stu-10")
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Sneha Sharma"


def test_get_student_cross_school_forbidden(other_teacher_client):
    from tests.conftest import mock_db
    mock_db.collection("students").document("stu-10").set({
        "school_id": "school-001",
        "class_id": "class-001",
        "student_code": "DPS-102",
        "name": "Sneha Sharma",
        "grade": "10",
        "section": "A",
        "status": "ACTIVE",
    })

    # other_teacher_client belongs to school-002
    res = other_teacher_client.get("/api/v1/students/stu-10")
    assert res.status_code == 403


def test_get_student_academic_subcollections(teacher_client):
    from tests.conftest import mock_db
    mock_db.collection("students").document("stu-10").set({
        "school_id": "school-001",
        "class_id": "class-001",
        "student_code": "DPS-102",
        "name": "Sneha Sharma",
        "grade": "10",
        "section": "A",
        "status": "ACTIVE",
    })

    # Direct subcollection insertion
    mock_db.collection("students").document("stu-10").collection("attendance").document("att-1").set({
        "student_id": "stu-10",
        "school_id": "school-001",
        "class_id": "class-001",
        "date": "2024-09-01",
        "status": "PRESENT",
        "source": "manual",
    })

    res = teacher_client.get("/api/v1/students/stu-10/attendance")
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1
    assert res.json()["data"][0]["status"] == "PRESENT"
