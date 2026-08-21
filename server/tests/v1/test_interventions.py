"""
tests/v1/test_interventions.py — Intervention API Tests
"""

import pytest


@pytest.fixture
def seed_student_for_intervention():
    from tests.conftest import mock_db
    mock_db.collection("students").document("stu-400").set({
        "school_id": "school-001",
        "class_id": "class-001",
        "student_code": "DPS-400",
        "name": "Kavya Patel",
        "grade": "10",
        "section": "A",
        "status": "ACTIVE",
    })
    mock_db.collection("classes").document("class-001").set({
        "school_id": "school-001",
        "name": "Class 10 - A",
        "grade": "10",
        "section": "A",
        "academic_year": "2024-25",
        "teacher_ids": ["teacher-uid-001"],
        "status": "ACTIVE",
    })


def test_create_intervention_success(teacher_client, seed_student_for_intervention):
    payload = {
        "student_id": "stu-400",
        "school_id": "school-001",
        "class_id": "class-001",
        "type": "ACADEMIC_SUPPORT",
        "notes": "Scheduled remedial math session for homework completion.",
        "follow_up_date": "2024-09-20",
    }
    response = teacher_client.post("/api/v1/interventions", json=payload)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["student_id"] == "stu-400"
    assert data["status"] == "PLANNED"
    assert data["type"] == "ACADEMIC_SUPPORT"
    assert "id" in data


def test_update_intervention_outcome(teacher_client, seed_student_for_intervention):
    # Create intervention first
    payload = {
        "student_id": "stu-400",
        "school_id": "school-001",
        "class_id": "class-001",
        "type": "PARENT_CONTACT",
        "notes": "Called parents regarding consecutive attendance drop.",
    }
    res = teacher_client.post("/api/v1/interventions", json=payload)
    int_id = res.json()["data"]["id"]

    # Update with outcome
    update_payload = {
        "status": "COMPLETED",
        "outcome": "STUDENT_IMPROVED",
        "outcome_notes": "Parents confirmed awareness; attendance restored to 100% next week.",
    }
    patch_res = teacher_client.patch(f"/api/v1/interventions/{int_id}", json=update_payload)
    assert patch_res.status_code == 200
    updated_data = patch_res.json()["data"]
    assert updated_data["status"] == "COMPLETED"
    assert updated_data["outcome"] == "STUDENT_IMPROVED"


def test_list_student_interventions(teacher_client, seed_student_for_intervention):
    payload = {
        "student_id": "stu-400",
        "school_id": "school-001",
        "class_id": "class-001",
        "type": "COUNSELING_REFERRAL",
        "notes": "Referred to student counselor.",
    }
    teacher_client.post("/api/v1/interventions", json=payload)

    res = teacher_client.get("/api/v1/interventions/student/stu-400")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) >= 1
    assert data[0]["student_id"] == "stu-400"


def test_cross_school_intervention_forbidden(other_teacher_client, seed_student_for_intervention):
    payload = {
        "student_id": "stu-400",
        "school_id": "school-001",
        "class_id": "class-001",
        "type": "ONE_ON_ONE_SUPPORT",
        "notes": "Attempt from unauthorized teacher.",
    }
    # other_teacher_client is from school-002
    response = other_teacher_client.post("/api/v1/interventions", json=payload)
    assert response.status_code == 403
