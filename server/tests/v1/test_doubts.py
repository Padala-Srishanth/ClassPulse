"""
tests/v1/test_doubts.py - Shared Doubt Discussion API Tests
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.schemas.class_ import ClassCreate
from app.schemas.student import StudentCreate
from app.services.class_service import ClassService
from app.services.student_service import StudentService
from app.services.doubt_service import DoubtService


def _setup_class_and_student(school_id="school-001"):
    cls_obj = ClassService.create_class(ClassCreate(
        school_id=school_id,
        name="Class 10-A Doubt Test",
        grade="10",
        section="A",
        academic_year="2026-27",
        teacher_ids=[],
    ))
    stu = StudentService.create_student(StudentCreate(
        student_code=f"DSTU-{cls_obj.id[:6]}",
        name="Rohan Doubt",
        school_id=school_id,
        class_id=cls_obj.id,
        grade="10",
        section="A",
    ))
    return cls_obj.id, stu.id


# ---------------------------------------------------------------------------
# Test 1: Student can post a doubt
# ---------------------------------------------------------------------------

def test_student_can_post_doubt(app, mock_student_token):
    class_id, student_id = _setup_class_and_student()
    mock_student_token["student_id"] = student_id
    mock_student_token["school_id"] = "school-001"

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_student_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            res = client.post("/api/v1/doubts", json={
                "class_id": class_id,
                "title": "What is integration by parts?",
                "body": "I cannot understand when to apply integration by parts. Can someone explain?",
                "subject": "Mathematics",
                "visibility": "CLASS",
            })
            assert res.status_code == 201, res.text
            data = res.json()["data"]
            assert data["title"] == "What is integration by parts?"
            assert data["status"] == "OPEN"
            assert data["reply_count"] == 0
            return data["id"]


# ---------------------------------------------------------------------------
# Test 2: Teacher cannot post a doubt via /doubts (teacher-facing endpoint requires student)
# ---------------------------------------------------------------------------

def test_teacher_cannot_post_doubt_on_student_endpoint(app, mock_teacher_token):
    class_id, _ = _setup_class_and_student()

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_teacher_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            res = client.post("/api/v1/doubts", json={
                "class_id": class_id,
                "title": "Teacher Should Not Post Doubt",
                "body": "This should be 403.",
                "subject": "Mathematics",
            })
            assert res.status_code == 403, res.text


# ---------------------------------------------------------------------------
# Test 3: Teacher can list class doubts
# ---------------------------------------------------------------------------

def test_teacher_can_list_class_doubts(app, mock_teacher_token):
    class_id, student_id = _setup_class_and_student()
    # Seed a doubt directly
    DoubtService.create_doubt(
        school_id="school-001",
        class_id=class_id,
        student_id=student_id,
        student_name="Rohan Doubt",
        title="Newton's 2nd Law",
        body="How does F=ma work?",
        subject="Physics",
    )

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_teacher_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            res = client.get(f"/api/v1/doubts?class_id={class_id}")
            assert res.status_code == 200, res.text
            doubts = res.json()["data"]
            assert len(doubts) >= 1
            assert any(d["title"] == "Newton's 2nd Law" for d in doubts)


# ---------------------------------------------------------------------------
# Test 4: Teacher can reply to a doubt
# ---------------------------------------------------------------------------

def test_teacher_can_reply_to_doubt(app, mock_teacher_token):
    class_id, student_id = _setup_class_and_student()
    doubt = DoubtService.create_doubt(
        school_id="school-001",
        class_id=class_id,
        student_id=student_id,
        student_name="Rohan Doubt",
        title="What is entropy?",
        body="Explain entropy in thermodynamics.",
        subject="Physics",
    )

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_teacher_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            res = client.post(f"/api/v1/doubts/{doubt.id}/replies", json={
                "body": "Entropy is a measure of disorder in a system. The second law states...",
            })
            assert res.status_code == 201, res.text
            reply_data = res.json()["data"]
            assert reply_data["body"] == "Entropy is a measure of disorder in a system. The second law states..."
            assert reply_data["author_role"] == "TEACHER"
            return doubt.id, reply_data["id"]


# ---------------------------------------------------------------------------
# Test 5: Teacher can mark a reply as verified answer
# ---------------------------------------------------------------------------

def test_teacher_can_mark_answer(app, mock_teacher_token):
    class_id, student_id = _setup_class_and_student()
    doubt = DoubtService.create_doubt(
        school_id="school-001",
        class_id=class_id,
        student_id=student_id,
        student_name="Rohan Doubt",
        title="What is photosynthesis?",
        body="Biology question about photosynthesis.",
        subject="Biology",
    )
    reply = DoubtService.add_reply(
        doubt_id=doubt.id,
        school_id="school-001",
        class_id=class_id,
        author_id="teacher-001",
        author_name="Ms. Sarah",
        author_role="TEACHER",
        body="Photosynthesis is the process by which plants convert light to food.",
    )

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_teacher_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            res = client.post(f"/api/v1/doubts/{doubt.id}/mark-answered?reply_id={reply.id}")
            assert res.status_code == 200, res.text
            updated_doubt = res.json()["data"]
            assert updated_doubt["status"] == "ANSWERED"
            assert updated_doubt["answered_by"] is not None


# ---------------------------------------------------------------------------
# Test 6: Teacher can close a doubt
# ---------------------------------------------------------------------------

def test_teacher_can_close_doubt(app, mock_teacher_token):
    class_id, student_id = _setup_class_and_student()
    doubt = DoubtService.create_doubt(
        school_id="school-001",
        class_id=class_id,
        student_id=student_id,
        student_name="Rohan Doubt",
        title="How to solve quadratic?",
        body="I need help with the quadratic formula.",
        subject="Mathematics",
    )

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_teacher_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            res = client.post(f"/api/v1/doubts/{doubt.id}/close")
            assert res.status_code == 200, res.text
            assert res.json()["data"]["status"] == "CLOSED"


# ---------------------------------------------------------------------------
# Test 7: Student cannot mark a reply as verified answer
# ---------------------------------------------------------------------------

def test_student_cannot_mark_answer(app, mock_student_token):
    class_id, student_id = _setup_class_and_student()
    mock_student_token["student_id"] = student_id
    mock_student_token["school_id"] = "school-001"

    doubt = DoubtService.create_doubt(
        school_id="school-001",
        class_id=class_id,
        student_id=student_id,
        student_name="Rohan Doubt",
        title="Student tries to mark answer",
        body="This should fail.",
        subject="Chemistry",
    )
    reply = DoubtService.add_reply(
        doubt_id=doubt.id,
        school_id="school-001",
        class_id=class_id,
        author_id="teacher-001",
        author_name="Ms. Sarah",
        author_role="TEACHER",
        body="A proper answer.",
    )

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_student_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            res = client.post(f"/api/v1/doubts/{doubt.id}/mark-answered?reply_id={reply.id}")
            assert res.status_code == 403, res.text


# ---------------------------------------------------------------------------
# Test 8: Principal can view school-wide stats
# ---------------------------------------------------------------------------

def test_principal_school_doubt_stats(app, mock_school_admin_token):
    class_id, student_id = _setup_class_and_student()
    DoubtService.create_doubt(
        school_id="school-001",
        class_id=class_id,
        student_id=student_id,
        student_name="Rohan Doubt",
        title="Stats Test Doubt",
        body="This doubt contributes to stats.",
        subject="Mathematics",
    )

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_school_admin_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            res = client.get("/api/v1/doubts/stats/school")
            assert res.status_code == 200, res.text
            stats = res.json()["data"]
            assert "total" in stats
            assert "open" in stats
            assert "answer_rate" in stats
            assert stats["total"] >= 1


# ---------------------------------------------------------------------------
# Test 9: Teacher can delete a doubt
# ---------------------------------------------------------------------------

def test_teacher_can_delete_doubt(app, mock_teacher_token):
    class_id, student_id = _setup_class_and_student()
    doubt = DoubtService.create_doubt(
        school_id="school-001",
        class_id=class_id,
        student_id=student_id,
        student_name="Rohan Doubt",
        title="This doubt will be deleted",
        body="Delete me.",
        subject="History",
    )

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_teacher_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            res = client.delete(f"/api/v1/doubts/{doubt.id}")
            assert res.status_code == 200, res.text
            assert res.json()["data"]["deleted"] is True

            # Verify it is actually gone
            get_res = client.get(f"/api/v1/doubts/{doubt.id}")
            assert get_res.status_code == 404, get_res.text


# ---------------------------------------------------------------------------
# Test 10: Student can post a doubt with a photo attachment
# ---------------------------------------------------------------------------

def test_student_can_post_doubt_with_photo(app, mock_student_token):
    class_id, student_id = _setup_class_and_student()
    mock_student_token["student_id"] = student_id
    mock_student_token["school_id"] = "school-001"

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_student_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            res = client.post("/api/v1/student/doubts", json={
                "class_id": class_id,
                "title": "Geometry Circle Theorem Question",
                "body": "Please see attached diagram for question 4.",
                "subject": "Mathematics",
                "attachment_name": "circle_theorem.png",
                "attachment_url": "/api/v1/uploads/files/circle_theorem.png",
                "visibility": "CLASS",
            })
            assert res.status_code == 201, res.text
            data = res.json()["data"]
            assert data["attachment_name"] == "circle_theorem.png"
            assert data["attachment_url"] == "/api/v1/uploads/files/circle_theorem.png"
            doubt_id = data["id"]

            # Verify when fetching detail, attachment fields are preserved
            detail_res = client.get(f"/api/v1/student/doubts/{doubt_id}")
            assert detail_res.status_code == 200, detail_res.text
            doubt_detail = detail_res.json()["data"]["doubt"]
            assert doubt_detail["attachment_name"] == "circle_theorem.png"
            assert doubt_detail["attachment_url"] == "/api/v1/uploads/files/circle_theorem.png"


# ---------------------------------------------------------------------------
# Test 11: Teacher and student can reply with a photo attachment
# ---------------------------------------------------------------------------

def test_reply_with_photo_attachment(app, mock_teacher_token):
    class_id, student_id = _setup_class_and_student()
    doubt = DoubtService.create_doubt(
        school_id="school-001",
        class_id=class_id,
        student_id=student_id,
        student_name="Rohan Doubt",
        title="Trigonometry proof",
        body="How to prove sin^2 + cos^2 = 1 geometrically?",
        subject="Mathematics",
    )

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_teacher_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            res = client.post(f"/api/v1/doubts/{doubt.id}/replies", json={
                "body": "Here is the unit circle geometrical proof:",
                "attachment_name": "unit_circle_proof.png",
                "attachment_url": "/api/v1/uploads/files/unit_circle_proof.png",
            })
            assert res.status_code == 201, res.text
            reply_data = res.json()["data"]
            assert reply_data["attachment_name"] == "unit_circle_proof.png"
            assert reply_data["attachment_url"] == "/api/v1/uploads/files/unit_circle_proof.png"
