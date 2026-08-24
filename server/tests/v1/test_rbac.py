"""
tests/v1/test_rbac.py — Role-Based Access Control & Tenant Isolation Tests
"""

import pytest


def test_student_cannot_access_teacher_endpoints(student_client):
    # Student cannot create student
    res = student_client.post("/api/v1/students", json={
        "school_id": "school-001",
        "class_id": "cls-1",
        "name": "Hacker Student",
        "student_code": "HACK01",
        "grade": "10",
        "section": "A",
    })
    assert res.status_code == 403


def test_student_can_access_student_portal(student_client):
    res = student_client.get("/api/v1/student/me")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["role"] == "STUDENT"


def test_teacher_cannot_access_student_portal(teacher_client):
    res = teacher_client.get("/api/v1/student/me")
    assert res.status_code == 403


def test_principal_can_create_all_school_announcement(school_admin_client):
    res = school_admin_client.post("/api/v1/announcements", json={
        "title": "School Reopens",
        "message": "School reopens Monday.",
        "target": "ALL_SCHOOL",
    })
    assert res.status_code == 201


def test_student_cannot_create_all_school_announcement(student_client):
    stu_res = student_client.post("/api/v1/announcements", json={
        "title": "Prank Announcement",
        "message": "No school tomorrow.",
        "target": "ALL_SCHOOL",
    })
    assert stu_res.status_code == 403


def test_read_announcements_for_each_role(school_admin_client):
    assert school_admin_client.get("/api/v1/announcements").status_code == 200


def test_read_announcements_for_teacher(teacher_client):
    assert teacher_client.get("/api/v1/announcements").status_code == 200


def test_read_announcements_for_student(student_client):
    assert student_client.get("/api/v1/announcements").status_code == 200
