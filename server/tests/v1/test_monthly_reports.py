"""
tests/v1/test_monthly_reports.py — API Integration & RBAC Tests for Monthly Reporting
"""

from unittest.mock import patch
import pytest

from app.models.class_ import Class, ClassStatus
from app.models.monthly_report import DataStatus, MonthlyStudentReport
from app.models.school import School, SchoolStatus
from app.models.student import Student, StudentStatus
from app.services.class_service import ClassService
from app.services.monthly_report_service import MonthlyReportService
from app.services.school_service import SchoolService
from app.services.student_service import StudentService


from app.core.firebase import get_firestore_client


@pytest.fixture(autouse=True)
def seed_test_entities():
    """Seed base school, class, and student in mock firestore."""
    db = get_firestore_client()
    # School
    s = School(
        id="school-001", name="DPS Demo Campus", code="DPS-001",
        district="Central", state="Delhi", country="India", status=SchoolStatus.ACTIVE,
    )
    db.collection("schools").document("school-001").set(s.to_firestore())

    # Class
    c = Class(
        id="class-001", school_id="school-001", name="10-A", grade="10", section="A",
        academic_year="2026-2027", teacher_ids=["teacher-uid-001"], status=ClassStatus.ACTIVE,
    )
    db.collection("classes").document("class-001").set(c.to_firestore())

    # Student 1 (matches mock_student_token)
    st1 = Student(
        id="demo-student-001", school_id="school-001", class_id="class-001",
        student_code="STU-001", name="Aarav Sharma", grade="10", section="A",
        status=StudentStatus.ACTIVE,
    )
    db.collection("students").document("demo-student-001").set(st1.to_firestore())

    # Student 2 (another student in class)
    st2 = Student(
        id="stu-002", school_id="school-001", class_id="class-001",
        student_code="STU-002", name="Diya Patel", grade="10", section="A",
        status=StudentStatus.ACTIVE,
    )
    db.collection("students").document("stu-002").set(st2.to_firestore())


def test_list_reporting_periods(teacher_client):
    res = teacher_client.get("/api/v1/monthly-reports/periods")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "periods" in data
    assert "2026-05" in data["periods"]


def test_get_student_monthly_report_student_self(student_client):
    res = student_client.get("/api/v1/monthly-reports/student/demo-student-001?report_period=2026-05")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["student_id"] == "demo-student-001"
    assert data["report_period"] == "2026-05"
    assert "attendance" in data
    assert "risk" in data


def test_student_cannot_access_other_student_report(student_client):
    # Student attempts to access stu-002
    res = student_client.get("/api/v1/monthly-reports/student/stu-002?report_period=2026-05")
    assert res.status_code == 403


def test_teacher_can_access_student_report(teacher_client):
    res = teacher_client.get("/api/v1/monthly-reports/student/stu-002?report_period=2026-05")
    assert res.status_code == 200
    assert res.json()["data"]["student_id"] == "stu-002"


def test_student_monthly_history(teacher_client):
    # Generate reports for two months
    MonthlyReportService.generate_student_report("demo-student-001", "2026-04", force=True)
    MonthlyReportService.generate_student_report("demo-student-001", "2026-05", force=True)

    res = teacher_client.get("/api/v1/monthly-reports/student/demo-student-001/history")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["count"] >= 2
    periods = [r["report_period"] for r in data["history"]]
    assert "2026-04" in periods
    assert "2026-05" in periods


def test_get_class_monthly_report(teacher_client):
    res = teacher_client.get("/api/v1/monthly-reports/class/class-001?report_period=2026-05")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["class_id"] == "class-001"
    assert data["report_period"] == "2026-05"
    assert "total_students" in data


def test_student_cannot_access_class_report(student_client):
    res = student_client.get("/api/v1/monthly-reports/class/class-001?report_period=2026-05")
    assert res.status_code == 403


def test_get_school_monthly_report_principal(school_admin_client):
    res = school_admin_client.get("/api/v1/monthly-reports/school/school-001?report_period=2026-05")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["school_id"] == "school-001"
    assert data["report_period"] == "2026-05"
    assert "class_comparisons" in data
    assert "student_risk_leaderboard" in data


def test_teacher_cannot_access_school_report(teacher_client):
    res = teacher_client.get("/api/v1/monthly-reports/school/school-001?report_period=2026-05")
    assert res.status_code == 403


def test_school_isolation_enforced(other_teacher_client):
    # Teacher from school-002 attempts to access class in school-001
    res = other_teacher_client.get("/api/v1/monthly-reports/class/class-001?report_period=2026-05")
    assert res.status_code == 403
