"""
tests/v1/test_schools.py — School API Tests
"""

import pytest


def test_create_school_admin(admin_client):
    payload = {
        "name": "Delhi Public School",
        "code": "DPS-DEL",
        "district": "South Delhi",
        "state": "Delhi",
        "country": "India",
    }
    response = admin_client.post("/api/v1/schools", json=payload)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "Delhi Public School"
    assert data["code"] == "DPS-DEL"
    assert "id" in data


def test_create_school_forbidden_for_teacher(teacher_client):
    payload = {
        "name": "Unauthorized School",
        "code": "UNAUTH",
    }
    response = teacher_client.post("/api/v1/schools", json=payload)
    assert response.status_code == 403


def test_get_school_success(admin_client):
    payload = {"name": "St. Marys", "code": "STM-01"}
    res = admin_client.post("/api/v1/schools", json=payload)
    school_id = res.json()["data"]["id"]

    get_res = admin_client.get(f"/api/v1/schools/{school_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["name"] == "St. Marys"


def test_get_school_cross_school_forbidden(other_teacher_client):
    from tests.conftest import mock_db
    mock_db.collection("schools").document("school-001").set({
        "name": "School One",
        "code": "SCH-1",
        "district": "Dist",
        "state": "State",
        "country": "India",
        "status": "ACTIVE",
    })

    # Teacher from school-002 tries to access school-001
    get_res = other_teacher_client.get("/api/v1/schools/school-001")
    assert get_res.status_code == 403



def test_update_school_success(school_admin_client, admin_client):
    # Create school with ID "school-001"
    from app.models.school import School, SchoolStatus
    from app.services.school_service import SchoolService
    from app.schemas.school import SchoolCreate

    # Mock DB direct entry for school-001
    from tests.conftest import mock_db
    mock_db.collection("schools").document("school-001").set({
        "name": "Old Name",
        "code": "SCH-1",
        "district": "Dist",
        "state": "State",
        "country": "India",
        "status": "ACTIVE",
    })

    update_payload = {"name": "New School Name"}
    res = school_admin_client.patch("/api/v1/schools/school-001", json=update_payload)
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "New School Name"


def test_list_schools_admin(admin_client):
    admin_client.post("/api/v1/schools", json={"name": "School A", "code": "SCH-A"})
    admin_client.post("/api/v1/schools", json={"name": "School B", "code": "SCH-B"})

    res = admin_client.get("/api/v1/schools")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) >= 2
