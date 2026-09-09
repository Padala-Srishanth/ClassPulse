"""
tests/v1/test_upcoming_exams.py — Upcoming Exams & Notification Logic Tests

Tests:
  - Past exams do NOT appear in upcoming
  - Exam today: days_remaining = 0, urgency = TODAY
  - Exam tomorrow: days_remaining = 1, urgency = TOMORROW
  - Exam in 5 days: urgency = THIS_WEEK
  - Exam in 30 days: urgency = UPCOMING
  - Student cannot create exams (403)
  - Cross-school access denied (403)
  - New scheduling fields work correctly
  - Backwards compat — exams without scheduling fields still work
"""

import datetime
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Date constants
# ---------------------------------------------------------------------------

TODAY = datetime.date.today().isoformat()
TOMORROW = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
IN_5_DAYS = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
IN_30_DAYS = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
YESTERDAY = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_class_and_exams(client_with_access, *exam_dates):
    """Create class + one exam per date, using a client that has class+exam create access.
    Returns (class_id, [exam_ids]).
    """
    res = client_with_access.post("/api/v1/classes", json={
        "school_id": "school-001",
        "name": "Grade 9-A",
        "grade": "9",
        "section": "A",
        "academic_year": "2026-27",
        "teacher_ids": [],
    })
    assert res.status_code == 201, res.text
    class_id = res.json()["data"]["id"]

    exam_ids = []
    for exam_date in exam_dates:
        res = client_with_access.post("/api/v1/exams", json={
            "school_id": "school-001",
            "class_id": class_id,
            "exam_name": f"Exam on {exam_date}",
            "subject": "Mathematics",
            "exam_date": exam_date,
            "max_marks": 100.0,
        })
        assert res.status_code == 201, res.text
        exam_ids.append(res.json()["data"]["id"])

    return class_id, exam_ids


# ---------------------------------------------------------------------------
# Student cannot create exams
# ---------------------------------------------------------------------------

def test_student_cannot_create_exam(app, mock_student_token, mock_school_admin_token):
    """Student role is blocked from creating exams."""
    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_school_admin_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as admin_c:
            class_id, _ = _create_class_and_exams(admin_c)

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_student_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as student_c:
            res = student_c.post("/api/v1/exams", json={
                "school_id": "school-001",
                "class_id": class_id,
                "exam_name": "Hacked Exam",
                "subject": "Hack",
                "exam_date": TOMORROW,
                "max_marks": 100.0,
            })
            assert res.status_code == 403


# ---------------------------------------------------------------------------
# Upcoming exam filtering — use school_admin_client (which has both class + exam access)
# ---------------------------------------------------------------------------

def test_past_exams_not_in_upcoming(school_admin_client):
    class_id, _ = _create_class_and_exams(school_admin_client, YESTERDAY)

    res = school_admin_client.get(f"/api/v1/exams/upcoming/my?class_id={class_id}")
    assert res.status_code == 200
    data = res.json()["data"]
    # No past exams
    assert all(e["exam_date"] >= TODAY for e in data)


def test_today_exam_has_zero_days_remaining(school_admin_client):
    class_id, _ = _create_class_and_exams(school_admin_client, TODAY)

    res = school_admin_client.get(f"/api/v1/exams/upcoming/my?class_id={class_id}")
    assert res.status_code == 200
    data = res.json()["data"]
    today_exams = [e for e in data if e["exam_date"] == TODAY]
    assert len(today_exams) >= 1
    assert today_exams[0]["days_remaining"] == 0
    assert today_exams[0]["urgency"] == "TODAY"


def test_tomorrow_exam_has_one_day_remaining(school_admin_client):
    class_id, _ = _create_class_and_exams(school_admin_client, TOMORROW)

    res = school_admin_client.get(f"/api/v1/exams/upcoming/my?class_id={class_id}")
    assert res.status_code == 200
    data = res.json()["data"]
    tomorrow_exams = [e for e in data if e["exam_date"] == TOMORROW]
    assert len(tomorrow_exams) >= 1
    assert tomorrow_exams[0]["days_remaining"] == 1
    assert tomorrow_exams[0]["urgency"] == "TOMORROW"


def test_this_week_exam_urgency(school_admin_client):
    class_id, _ = _create_class_and_exams(school_admin_client, IN_5_DAYS)

    res = school_admin_client.get(f"/api/v1/exams/upcoming/my?class_id={class_id}")
    assert res.status_code == 200
    data = res.json()["data"]
    week_exams = [e for e in data if e["exam_date"] == IN_5_DAYS]
    assert len(week_exams) >= 1
    assert week_exams[0]["urgency"] == "THIS_WEEK"
    assert week_exams[0]["days_remaining"] == 5


def test_future_exam_urgency_upcoming(school_admin_client):
    class_id, _ = _create_class_and_exams(school_admin_client, IN_30_DAYS)

    res = school_admin_client.get(f"/api/v1/exams/upcoming/my?class_id={class_id}")
    assert res.status_code == 200
    data = res.json()["data"]
    future_exams = [e for e in data if e["exam_date"] == IN_30_DAYS]
    assert len(future_exams) >= 1
    assert future_exams[0]["urgency"] == "UPCOMING"
    assert future_exams[0]["days_remaining"] == 30


def test_upcoming_exams_ordered_by_date(school_admin_client):
    class_id, _ = _create_class_and_exams(school_admin_client, IN_30_DAYS, IN_5_DAYS, TOMORROW)

    res = school_admin_client.get(f"/api/v1/exams/upcoming/my?class_id={class_id}")
    assert res.status_code == 200
    data = res.json()["data"]
    dates = [e["exam_date"] for e in data]
    assert dates == sorted(dates)  # must be ascending


# ---------------------------------------------------------------------------
# New exam fields (start_time, end_time, description)
# ---------------------------------------------------------------------------

def test_create_exam_with_scheduling_fields(school_admin_client):
    class_id, _ = _create_class_and_exams(school_admin_client)

    res = school_admin_client.post("/api/v1/exams", json={
        "school_id": "school-001",
        "class_id": class_id,
        "exam_name": "Mid-Term Math",
        "subject": "Mathematics",
        "exam_date": TOMORROW,
        "max_marks": 100.0,
        "start_time": "10:00",
        "end_time": "11:30",
        "description": "Covers chapters 1 to 5",
    })
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["start_time"] == "10:00"
    assert data["end_time"] == "11:30"
    assert data["description"] == "Covers chapters 1 to 5"


def test_create_exam_without_scheduling_fields_still_works(school_admin_client):
    """Existing callers without time fields must still work (backwards compat)."""
    class_id, _ = _create_class_and_exams(school_admin_client)

    res = school_admin_client.post("/api/v1/exams", json={
        "school_id": "school-001",
        "class_id": class_id,
        "exam_name": "Quick Test",
        "subject": "Science",
        "exam_date": TOMORROW,
        "max_marks": 50.0,
    })
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["start_time"] is None
    assert data["end_time"] is None
    assert data["description"] is None


# ---------------------------------------------------------------------------
# Cross-school access
# ---------------------------------------------------------------------------

def test_cross_school_upcoming_exams_denied(app, mock_other_teacher_token, mock_school_admin_token):
    """Teacher from school-002 cannot access school-001 class exams."""
    # Create class and exam as school-001 admin
    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_school_admin_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as admin_c:
            class_id, _ = _create_class_and_exams(admin_c, TOMORROW)

    # Try to access as school-002 teacher
    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_other_teacher_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as t2_c:
            res = t2_c.get(f"/api/v1/exams/upcoming/my?class_id={class_id}")
            assert res.status_code == 403
