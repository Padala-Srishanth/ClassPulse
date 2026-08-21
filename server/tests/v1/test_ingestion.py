"""
tests/v1/test_ingestion.py — CSV Ingestion API Tests
"""

import io
import pytest


@pytest.fixture
def setup_students_in_db():
    from tests.conftest import mock_db
    mock_db.collection("students").document("stu-101").set({
        "school_id": "school-001",
        "class_id": "class-001",
        "student_code": "DPS-101",
        "name": "Rahul Kumar",
        "grade": "10",
        "section": "A",
        "status": "ACTIVE",
    })
    mock_db.collection("students").document("stu-102").set({
        "school_id": "school-001",
        "class_id": "class-001",
        "student_code": "DPS-102",
        "name": "Sneha Sharma",
        "grade": "10",
        "section": "A",
        "status": "ACTIVE",
    })


def test_ingest_attendance_success(teacher_client, setup_students_in_db):
    csv_content = (
        "student_code,date,status\n"
        "DPS-101,2024-09-01,PRESENT\n"
        "DPS-102,2024-09-01,ABSENT\n"
    )
    files = {"file": ("attendance.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    data = {"school_id": "school-001"}

    response = teacher_client.post("/api/v1/ingestion/attendance", data=data, files=files)
    assert response.status_code == 200
    summary = response.json()["data"]
    assert summary["total_rows"] == 2
    assert summary["successful_rows"] == 2
    assert summary["failed_rows"] == 0
    assert summary["duplicate_rows"] == 0


def test_ingest_attendance_duplicate_handling(teacher_client, setup_students_in_db):
    csv_content = (
        "student_code,date,status\n"
        "DPS-101,2024-09-01,PRESENT\n"
        "DPS-101,2024-09-01,PRESENT\n"  # duplicate in same file
    )
    files = {"file": ("attendance.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    data = {"school_id": "school-001"}

    response = teacher_client.post("/api/v1/ingestion/attendance", data=data, files=files)
    assert response.status_code == 200
    summary = response.json()["data"]
    assert summary["total_rows"] == 2
    assert summary["successful_rows"] == 1
    assert summary["duplicate_rows"] == 1


def test_ingest_attendance_invalid_rows(teacher_client, setup_students_in_db):
    csv_content = (
        "student_code,date,status\n"
        "DPS-101,invalid-date,PRESENT\n"
        "UNKNOWN-999,2024-09-01,PRESENT\n"
        "DPS-102,2024-09-01,INVALID_STATUS\n"
    )
    files = {"file": ("attendance.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    data = {"school_id": "school-001"}

    response = teacher_client.post("/api/v1/ingestion/attendance", data=data, files=files)
    assert response.status_code == 200
    summary = response.json()["data"]
    assert summary["total_rows"] == 3
    assert summary["successful_rows"] == 0
    assert summary["failed_rows"] == 3
    assert len(summary["errors"]) == 3


def test_ingest_homework_success(teacher_client, setup_students_in_db):
    csv_content = (
        "student_code,assignment_id,assignment_date,status\n"
        "DPS-101,HW-01,2024-09-02,COMPLETED\n"
        "DPS-102,HW-01,2024-09-02,LATE\n"
    )
    files = {"file": ("homework.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    data = {"school_id": "school-001"}

    response = teacher_client.post("/api/v1/ingestion/homework", data=data, files=files)
    assert response.status_code == 200
    summary = response.json()["data"]
    assert summary["successful_rows"] == 2


def test_ingest_test_scores_success_and_validation(teacher_client, setup_students_in_db):
    csv_content = (
        "student_code,subject,assessment_name,assessment_date,score,max_score\n"
        "DPS-101,Mathematics,Unit Test 1,2024-09-05,45,50\n"
        "DPS-102,Mathematics,Unit Test 1,2024-09-05,55,50\n"  # score > max_score
    )
    files = {"file": ("test_scores.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    data = {"school_id": "school-001"}

    response = teacher_client.post("/api/v1/ingestion/test-scores", data=data, files=files)
    assert response.status_code == 200
    summary = response.json()["data"]
    assert summary["successful_rows"] == 1
    assert summary["failed_rows"] == 1
    assert "exceeds max score" in summary["errors"][0]["error"]


def test_ingest_cross_school_forbidden(other_teacher_client):
    csv_content = "student_code,date,status\nDPS-101,2024-09-01,PRESENT\n"
    files = {"file": ("attendance.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    data = {"school_id": "school-001"}

    # other_teacher_client is from school-002
    response = other_teacher_client.post("/api/v1/ingestion/attendance", data=data, files=files)
    assert response.status_code == 403


def test_ingest_non_csv_rejected(teacher_client):
    files = {"file": ("test.txt", io.BytesIO(b"some content"), "text/plain")}
    data = {"school_id": "school-001"}

    response = teacher_client.post("/api/v1/ingestion/attendance", data=data, files=files)
    assert response.status_code == 400


def test_ingest_empty_file_rejected(teacher_client):
    files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
    data = {"school_id": "school-001"}

    response = teacher_client.post("/api/v1/ingestion/attendance", data=data, files=files)
    assert response.status_code == 400
