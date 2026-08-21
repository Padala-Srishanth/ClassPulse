"""
seed_demo_data.py — ClassPulse Demo Data Populator
Populates realistic benchmark school, class, students, and 4 weeks of academic records in Firestore.
"""

import os
import sys
from datetime import datetime, timezone
import uuid

# Ensure server package path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings
from app.core.firebase import get_firestore_client
from app.models.academic import AttendanceRecord, HomeworkRecord, TestScoreRecord
from app.models.class_ import Class
from app.models.intervention import Intervention, InterventionOutcome, InterventionStatus, InterventionType
from app.models.school import School
from app.models.student import Student
from app.models.user import User, UserRole
from app.services.risk_service import RiskService


def seed_database():
    print("🌱 Initializing Firestore client...")
    db = get_firestore_client()
    school_id = "school-001"
    class_id = "class-10a"

    # 1. School
    print("🏫 Seeding School...")
    school = School(
        id=school_id,
        name="Delhi Public Academy (Greenwood)",
        code="DPA-001",
        district="South Zone",
        state="Delhi",
        country="India",
        status="ACTIVE",
    )
    db.collection("schools").document(school_id).set(school.to_firestore())

    # 2. Users
    print("👤 Seeding Users (Admin, Principal, Teacher)...")
    teacher_user = User(
        id="teacher-uid-001",
        firebase_uid="teacher-uid-001",
        email="teacher@school-001.example.com",
        name="Sarah Jenkins",
        role=UserRole.TEACHER,
        school_id=school_id,
        status="ACTIVE",
    )
    db.collection("users").document("teacher-uid-001").set(teacher_user.to_firestore())

    principal_user = User(
        id="sadmin-uid-001",
        firebase_uid="sadmin-uid-001",
        email="principal@school-001.example.com",
        name="Dr. Evelyn Reed",
        role=UserRole.SCHOOL_ADMIN,
        school_id=school_id,
        status="ACTIVE",
    )
    db.collection("users").document("sadmin-uid-001").set(principal_user.to_firestore())

    # 3. Class
    print("📚 Seeding Class 10-A...")
    class_obj = Class(
        id=class_id,
        school_id=school_id,
        name="Class 10 - Section A",
        grade="10",
        section="A",
        academic_year="2024-25",
        teacher_ids=["teacher-uid-001"],
        status="ACTIVE",
    )
    db.collection("classes").document(class_id).set(class_obj.to_firestore())

    # 4. Students
    print("🎓 Seeding Students & Longitudinal Academic Signatures...")
    students_data = [
        {"id": "stu-101", "code": "DPS-101", "name": "Rahul Sharma", "profile": "SHARP_DROP"},
        {"id": "stu-102", "code": "DPS-102", "name": "Priya Nair", "profile": "GRADUAL_DECLINE"},
        {"id": "stu-103", "code": "DPS-103", "name": "Aarav Patel", "profile": "STABLE_HIGH"},
        {"id": "stu-104", "code": "DPS-104", "name": "Ananya Roy", "profile": "IMPROVING"},
        {"id": "stu-105", "code": "DPS-105", "name": "Vikram Malhotra", "profile": "NATURALLY_LOW_STABLE"},
    ]

    dates_w1 = ["2024-07-22", "2024-07-23", "2024-07-24", "2024-07-25", "2024-07-26"]
    dates_w2 = ["2024-07-29", "2024-07-30", "2024-07-31", "2024-08-01", "2024-08-02"]
    dates_w3 = ["2024-08-05", "2024-08-06", "2024-08-07", "2024-08-08", "2024-08-09"]
    dates_w4 = ["2024-08-12", "2024-08-13", "2024-08-14", "2024-08-15", "2024-08-16"]

    for s_info in students_data:
        s_id = s_info["id"]
        stu = Student(
            id=s_id,
            school_id=school_id,
            class_id=class_id,
            student_code=s_info["code"],
            name=s_info["name"],
            grade="10",
            section="A",
            status="ACTIVE",
        )
        db.collection("students").document(s_id).set(stu.to_firestore())

        # Seed subcollection data based on trajectory
        profile = s_info["profile"]

        # Helper to seed attendance
        def add_att(dates, status_list):
            for d, st in zip(dates, status_list):
                att_id = AttendanceRecord.make_id(s_id, d)
                rec = AttendanceRecord(id=att_id, student_id=s_id, school_id=school_id, class_id=class_id, date=d, status=st, source="csv")
                db.collection("students").document(s_id).collection("attendance").document(att_id).set(rec.to_firestore())

        # Helper to seed homework
        def add_hw(assign_id, date, status):
            hw_id = HomeworkRecord.make_id(s_id, assign_id, date)
            rec = HomeworkRecord(id=hw_id, student_id=s_id, school_id=school_id, class_id=class_id, assignment_id=assign_id, assignment_date=date, status=status, source="csv")
            db.collection("students").document(s_id).collection("homework").document(hw_id).set(rec.to_firestore())

        # Helper to seed test scores
        def add_test(subject, name, date, score, max_score):
            t_id = TestScoreRecord.make_id(s_id, subject, name, date)
            rec = TestScoreRecord(id=t_id, student_id=s_id, school_id=school_id, class_id=class_id, subject=subject, assessment_name=name, assessment_date=date, score=score, max_score=max_score, percentage=round(score/max_score*100, 1), source="csv")
            db.collection("students").document(s_id).collection("test_scores").document(t_id).set(rec.to_firestore())

        if profile == "SHARP_DROP":  # Rahul: Baseline 95% -> Recent 40%
            add_att(dates_w1, ["PRESENT"] * 5)
            add_att(dates_w2, ["PRESENT"] * 5)
            add_att(dates_w3, ["ABSENT", "ABSENT", "PRESENT", "ABSENT", "ABSENT"])
            add_att(dates_w4, ["ABSENT", "ABSENT", "ABSENT", "ABSENT", "PRESENT"])

            add_hw("HW-01", "2024-07-24", "COMPLETED")
            add_hw("HW-02", "2024-07-31", "COMPLETED")
            add_hw("HW-03", "2024-08-07", "MISSING")
            add_hw("HW-04", "2024-08-14", "MISSING")

            add_test("Math", "Unit Test 1", "2024-07-26", 48, 50)
            add_test("Science", "Unit Test 1", "2024-08-02", 45, 50)
            add_test("Math", "Midterm Quiz", "2024-08-16", 18, 50)

        elif profile == "GRADUAL_DECLINE":  # Priya: Baseline 90% -> 75% -> 60%
            add_att(dates_w1, ["PRESENT"] * 5)
            add_att(dates_w2, ["PRESENT", "PRESENT", "ABSENT", "PRESENT", "PRESENT"])
            add_att(dates_w3, ["PRESENT", "ABSENT", "PRESENT", "ABSENT", "PRESENT"])
            add_att(dates_w4, ["ABSENT", "PRESENT", "ABSENT", "PRESENT", "ABSENT"])

            add_hw("HW-01", "2024-07-24", "COMPLETED")
            add_hw("HW-02", "2024-07-31", "COMPLETED")
            add_hw("HW-03", "2024-08-07", "MISSING")
            add_hw("HW-04", "2024-08-14", "MISSING")

            add_test("English", "Unit 1", "2024-07-26", 42, 50)
            add_test("English", "Unit 2", "2024-08-16", 32, 50)

        else:  # Stable / Improving / Naturally Low
            add_att(dates_w1, ["PRESENT"] * 5)
            add_att(dates_w2, ["PRESENT"] * 5)
            add_att(dates_w3, ["PRESENT"] * 5)
            add_att(dates_w4, ["PRESENT"] * 5)

            add_hw("HW-01", "2024-07-24", "COMPLETED")
            add_hw("HW-02", "2024-07-31", "COMPLETED")
            add_hw("HW-03", "2024-08-07", "COMPLETED")
            add_hw("HW-04", "2024-08-14", "COMPLETED")

            add_test("Math", "Unit 1", "2024-07-26", 45, 50)
            add_test("Math", "Unit 2", "2024-08-16", 47, 50)

    # 5. Run AI Risk Analysis across Class 10-A
    print("🤖 Executing AI Risk Engine over cohort...")
    RiskService.analyze_class_cohort(class_id)

    # 6. Seed a sample intervention
    print("📋 Seeding sample intervention for Rahul Sharma...")
    int_id = str(uuid.uuid4())
    intervention = Intervention(
        id=int_id,
        school_id=school_id,
        student_id="stu-101",
        teacher_id="teacher-uid-001",
        class_id=class_id,
        type=InterventionType.PARENT_CONTACT,
        notes="Called mother regarding attendance drop over past two weeks. Agreed on follow-up check-in next Monday.",
        follow_up_date="2024-08-26",
        status=InterventionStatus.IN_PROGRESS,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )
    db.collection("interventions").document(int_id).set(intervention.to_firestore())

    print("\n✅ DEMO DATA SEEDED SUCCESSFULLY!")
    print("👉 Open http://localhost:5173/ to view Class 10-A live!")


if __name__ == "__main__":
    seed_database()
