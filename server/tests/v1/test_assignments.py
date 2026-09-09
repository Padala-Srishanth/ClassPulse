"""
tests/v1/test_assignments.py — Assignments and Classwork API Tests
"""

import datetime as dt_mod
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.schemas.class_ import ClassCreate
from app.schemas.student import StudentCreate
from app.services.class_service import ClassService
from app.services.student_service import StudentService
from app.services.assignment_service import AssignmentService


def _setup_class_and_student():
    """Seed a test class and student directly via services."""
    today = dt_mod.date.today().isoformat()
    cls_obj = ClassService.create_class(
        ClassCreate(
            school_id="school-001",
            name="Class 10-A",
            grade="10",
            section="A",
            academic_year="2026-27",
            teacher_ids=[],
        )
    )

    stu = StudentService.create_student(
        StudentCreate(
            student_code=f"STU-{cls_obj.id[:6]}",
            name="Aarav Sharma",
            school_id="school-001",
            class_id=cls_obj.id,
            grade="10",
            section="A",
        )
    )
    return cls_obj.id, stu.id


def test_teacher_can_create_assignment(app, mock_teacher_token):
    class_id, _ = _setup_class_and_student()
    future_date = (dt_mod.date.today() + dt_mod.timedelta(days=7)).isoformat()

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_teacher_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            res = client.post("/api/v1/assignments", json={
                "class_id": class_id,
                "title": "Quadratic Equations Problem Set",
                "subject": "Mathematics",
                "description": "Complete problems 1 through 15 on page 42.",
                "due_date": future_date,
                "due_time": "23:59",
                "max_marks": 25.0,
                "attachments": [
                    {"title": "algebra_worksheet.pdf", "url": "https://example.com/algebra.pdf", "file_type": "pdf"}
                ],
            })

            assert res.status_code == 201, res.text
            data = res.json()["data"]
            assert data["title"] == "Quadratic Equations Problem Set"
            assert data["subject"] == "Mathematics"
            assert data["max_marks"] == 25.0
            assert len(data["attachments"]) == 1


def test_student_cannot_create_assignment(app, mock_student_token):
    class_id, _ = _setup_class_and_student()
    future_date = (dt_mod.date.today() + dt_mod.timedelta(days=7)).isoformat()

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_student_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            res = client.post("/api/v1/assignments", json={
                "class_id": class_id,
                "title": "Student Hacked Assignment",
                "subject": "Mathematics",
                "due_date": future_date,
                "max_marks": 20.0,
            })
            assert res.status_code == 403


def test_teacher_can_list_and_update_assignment(app, mock_teacher_token):
    class_id, _ = _setup_class_and_student()
    future_date = (dt_mod.date.today() + dt_mod.timedelta(days=5)).isoformat()

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_teacher_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            res = client.post("/api/v1/assignments", json={
                "class_id": class_id,
                "title": "Physics Optics Lab",
                "subject": "Physics",
                "due_date": future_date,
                "max_marks": 20.0,
            })
            assert res.status_code == 201
            assignment_id = res.json()["data"]["id"]

            # List
            list_res = client.get(f"/api/v1/assignments?class_id={class_id}")
            assert list_res.status_code == 200
            assert any(a["id"] == assignment_id for a in list_res.json()["data"])

            # Update
            update_res = client.put(f"/api/v1/assignments/{assignment_id}", json={
                "title": "Physics Optics Lab Report (Revised)",
                "description": "Submit ray diagrams.",
            })
            assert update_res.status_code == 200
            assert update_res.json()["data"]["title"] == "Physics Optics Lab Report (Revised)"

            # Delete
            del_res = client.delete(f"/api/v1/assignments/{assignment_id}")
            assert del_res.status_code == 200

            # Verify deleted
            get_res = client.get(f"/api/v1/assignments/{assignment_id}")
            assert get_res.status_code == 404


def test_student_portal_lists_class_assignments(app, mock_student_token):
    class_id, student_id = _setup_class_and_student()
    future_date = (dt_mod.date.today() + dt_mod.timedelta(days=3)).isoformat()

    # Pre-seed assignment
    AssignmentService.create_assignment(
        school_id="school-001",
        class_id=class_id,
        teacher_id="teacher-uid-001",
        teacher_name="Sarah Jenkins",
        title="Chemistry Lab Writeup",
        subject="Chemistry",
        due_date=future_date,
        max_marks=20.0,
    )

    token = dict(mock_student_token)
    token["student_id"] = student_id

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            res = client.get("/api/v1/student/assignments")
            assert res.status_code == 200, res.text
            data = res.json()["data"]
            assert data["total_assigned"] >= 1
            assert len(data["pending"]) >= 1


def test_student_cannot_access_other_class_assignments(app, mock_student_token):
    class_id, student_id = _setup_class_and_student()
    other_class = ClassService.create_class(
        ClassCreate(
            school_id="school-001",
            name="Class 12-A",
            grade="12",
            section="A",
            academic_year="2026-27",
            teacher_ids=[],
        )
    )

    token = dict(mock_student_token)
    token["student_id"] = student_id

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            res = client.get(f"/api/v1/student/assignments?class_id={other_class.id}")
            assert res.status_code == 403
            assert res.json()["detail"]["code"] == "STUDENT_CLASS_MISMATCH"


def test_student_submit_assignment_on_time_and_late(app, mock_student_token):
    class_id, student_id = _setup_class_and_student()
    token = dict(mock_student_token)
    token["student_id"] = student_id

    # 1. On-time assignment (future deadline)
    future_date = (dt_mod.date.today() + dt_mod.timedelta(days=2)).isoformat()
    assign1 = AssignmentService.create_assignment(
        school_id="school-001",
        class_id=class_id,
        teacher_id="teacher-uid-001",
        teacher_name="Sarah Jenkins",
        title="Trigonometry Exercise",
        subject="Mathematics",
        due_date=future_date,
        due_time="23:59",
        max_marks=20.0,
    )

    # 2. Late assignment (past deadline)
    past_date = (dt_mod.date.today() - dt_mod.timedelta(days=2)).isoformat()
    assign2 = AssignmentService.create_assignment(
        school_id="school-001",
        class_id=class_id,
        teacher_id="teacher-uid-001",
        teacher_name="Sarah Jenkins",
        title="History Essay",
        subject="History",
        due_date=past_date,
        due_time="23:59",
        max_marks=20.0,
    )

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            # Submit on-time
            sub1_res = client.post(f"/api/v1/student/assignments/{assign1.id}/submit", json={
                "content": "All answers solved in attached doc.",
                "attachment_name": "trig_answers.pdf",
                "attachment_url": "https://example.com/trig.pdf",
            })
            assert sub1_res.status_code == 200, sub1_res.text
            sub1_data = sub1_res.json()["data"]
            assert sub1_data["is_late"] is False
            assert sub1_data["status"] == "SUBMITTED"

            # Submit late
            sub2_res = client.post(f"/api/v1/student/assignments/{assign2.id}/submit", json={
                "content": "Apologies for late submission.",
                "attachment_name": "history_essay.pdf",
            })
            assert sub2_res.status_code == 200, sub2_res.text
            sub2_data = sub2_res.json()["data"]
            assert sub2_data["is_late"] is True
            assert sub2_data["status"] == "LATE"


def test_teacher_grades_submission(app, mock_teacher_token, mock_student_token):
    class_id, student_id = _setup_class_and_student()
    future_date = (dt_mod.date.today() + dt_mod.timedelta(days=3)).isoformat()
    assign = AssignmentService.create_assignment(
        school_id="school-001",
        class_id=class_id,
        teacher_id="teacher-uid-001",
        teacher_name="Sarah Jenkins",
        title="English Poem Interpretation",
        subject="English",
        due_date=future_date,
        max_marks=20.0,
    )

    # Student submits
    token = dict(mock_student_token)
    token["student_id"] = student_id
    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            client.post(f"/api/v1/student/assignments/{assign.id}/submit", json={
                "content": "My poetic analysis.",
            })

    # Teacher reviews and grades
    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_teacher_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            # Check submissions list
            subs_res = client.get(f"/api/v1/assignments/{assign.id}/submissions")
            assert subs_res.status_code == 200
            roster = subs_res.json()["data"]
            assert len(roster) >= 1

            # Grade submission
            grade_res = client.put(f"/api/v1/assignments/{assign.id}/submissions/{student_id}/grade", json={
                "obtained_marks": 18.5,
                "feedback": "Excellent thematic breakdown!",
            })
            assert grade_res.status_code == 200
            graded_data = grade_res.json()["data"]
            assert graded_data["obtained_marks"] == 18.5
            assert graded_data["feedback"] == "Excellent thematic breakdown!"
            assert graded_data["status"] == "GRADED"

            # Rejection of marks > max_marks
            invalid_grade_res = client.put(f"/api/v1/assignments/{assign.id}/submissions/{student_id}/grade", json={
                "obtained_marks": 99.0,
                "feedback": "Too high",
            })
            assert invalid_grade_res.status_code == 400


def test_principal_can_view_assignment_stats(app, mock_school_admin_token):
    class_id, _ = _setup_class_and_student()
    future_date = (dt_mod.date.today() + dt_mod.timedelta(days=4)).isoformat()
    AssignmentService.create_assignment(
        school_id="school-001",
        class_id=class_id,
        teacher_id="teacher-uid-001",
        teacher_name="Sarah Jenkins",
        title="Biology Cell Division Chart",
        subject="Biology",
        due_date=future_date,
        max_marks=15.0,
    )

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_school_admin_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            res = client.get("/api/v1/assignments/stats/overview")
            assert res.status_code == 200, res.text
            data = res.json()["data"]
            assert data["total_assignments"] >= 1
            assert "classes" in data
            assert isinstance(data["classes"], list)
