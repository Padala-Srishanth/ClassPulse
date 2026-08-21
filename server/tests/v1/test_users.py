"""
tests/v1/test_users.py — User API Tests
"""

import pytest


def test_create_user_admin(admin_client):
    payload = {
        "firebase_uid": "teacher-uid-100",
        "email": "teacher100@school.com",
        "name": "Jane Teacher",
        "role": "TEACHER",
        "school_id": "school-001",
    }
    response = admin_client.post("/api/v1/users", json=payload)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "Jane Teacher"
    assert data["role"] == "TEACHER"


def test_create_user_school_admin_isolation(school_admin_client):
    # School admin is for school-001. Trying to create a user for school-002 should fail.
    payload = {
        "firebase_uid": "teacher-uid-200",
        "email": "teacher200@school.com",
        "name": "Other Teacher",
        "role": "TEACHER",
        "school_id": "school-002",
    }
    response = school_admin_client.post("/api/v1/users", json=payload)
    assert response.status_code == 403


def test_get_my_profile(teacher_client, mock_teacher_token):
    # Create profile in DB first
    from tests.conftest import mock_db
    mock_db.collection("users").document(mock_teacher_token["uid"]).set({
        "firebase_uid": mock_teacher_token["uid"],
        "email": mock_teacher_token["email"],
        "name": "Teacher One",
        "role": "TEACHER",
        "school_id": "school-001",
        "status": "ACTIVE",
    })

    res = teacher_client.get("/api/v1/users/me")
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Teacher One"


def test_list_school_users(school_admin_client):
    from tests.conftest import mock_db
    mock_db.collection("users").document("u1").set({
        "firebase_uid": "u1", "email": "u1@school.com", "name": "User 1",
        "role": "TEACHER", "school_id": "school-001", "status": "ACTIVE",
    })
    mock_db.collection("users").document("u2").set({
        "firebase_uid": "u2", "email": "u2@school.com", "name": "User 2",
        "role": "TEACHER", "school_id": "school-001", "status": "ACTIVE",
    })

    res = school_admin_client.get("/api/v1/users/school/school-001")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) == 2
