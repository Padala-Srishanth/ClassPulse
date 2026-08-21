"""
tests/v1/test_classes.py — Class API Tests
"""

import pytest


def test_create_class_school_admin(school_admin_client):
    payload = {
        "school_id": "school-001",
        "name": "Class 10 - Section A",
        "grade": "10",
        "section": "A",
        "academic_year": "2024-25",
        "teacher_ids": ["teacher-uid-001"],
    }
    response = school_admin_client.post("/api/v1/classes", json=payload)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "Class 10 - Section A"
    assert data["school_id"] == "school-001"
    assert "id" in data


def test_create_class_cross_school_forbidden(school_admin_client):
    payload = {
        "school_id": "school-002",
        "name": "Class 10 - Section B",
        "grade": "10",
        "section": "B",
        "academic_year": "2024-25",
    }
    response = school_admin_client.post("/api/v1/classes", json=payload)
    assert response.status_code == 403


def test_get_class_details(teacher_client):
    from tests.conftest import mock_db
    mock_db.collection("classes").document("class-001").set({
        "school_id": "school-001",
        "name": "Class 9 - A",
        "grade": "9",
        "section": "A",
        "academic_year": "2024-25",
        "teacher_ids": ["teacher-uid-001"],
        "status": "ACTIVE",
    })

    res = teacher_client.get("/api/v1/classes/class-001")
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Class 9 - A"


def test_list_school_classes(school_admin_client):
    from tests.conftest import mock_db
    mock_db.collection("classes").document("c1").set({
        "school_id": "school-001", "name": "Class 8 - A", "grade": "8",
        "section": "A", "academic_year": "2024-25", "teacher_ids": [], "status": "ACTIVE"
    })
    mock_db.collection("classes").document("c2").set({
        "school_id": "school-001", "name": "Class 8 - B", "grade": "8",
        "section": "B", "academic_year": "2024-25", "teacher_ids": [], "status": "ACTIVE"
    })

    res = school_admin_client.get("/api/v1/classes/school/school-001")
    assert res.status_code == 200
    assert len(res.json()["data"]) == 2
