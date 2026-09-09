"""
seed_demo_data.py — ClassPulse Comprehensive Demo Data Generator

Generates a realistic benchmark school (Delhi Public School - Demo Campus) with:
- 1 School (school-001)
- 14 Classes across Grades 6 to 12 (6-A, 6-B, 7-A, 7-B, ..., 12-A, 12-B)
- 35 Teachers across 9 subjects with class teacher assignments
- 1 Principal (Sarah Jenkins, SCHOOL_ADMIN)
- ~630 Students with realistic profiles and parent contacts
- 10 weeks (50 weekdays) of realistic attendance history per student
- 10 weeks of homework completion records
- 4 Major Exams per class (Unit Test 1, Unit Test 2, Mid-Term, Unit Test 3) + results
- Full synthetic benchmark cohorts for the AI Risk Engine:
    1. SUDDEN DROP (High Risk)
    2. GRADUAL DECLINE (High/Medium Risk)
    3. STABLE HIGH PERFORMER (Low Risk)
    4. IMPROVING STUDENT (Low/Improving)
    5. NATURALLY LOW BUT STABLE (Low/Stable)
    6. TEMPORARY DIP (Low/Transient)
    7. MISSING DATA / NEW ADMISSION (Needs Data)
- Remedial & Preventive Interventions
- School-wide, Teacher-specific, Student-specific, and Class-specific Announcements
- Appointment & Meeting Requests (Student <-> Teacher, Student <-> Principal)
- Complete pre-computed AI Risk Analysis & Alerts for all classes

Usage:
    python seed_demo_data.py [--school-id school-001] [--reset] [--seed]
"""

from __future__ import annotations

import argparse
import hashlib
import os
import random
import sys
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

# Ensure server package path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings
from app.core.firebase import get_firestore_client, initialise_firebase
from app.models.academic import (
    AttendanceRecord,
    AttendanceStatus,
    HomeworkRecord,
    HomeworkStatus,
    TestScoreRecord,
)
from app.models.announcement import Announcement, AnnouncementTarget
from app.models.assignment import Assignment, AssignmentStatus, AssignmentSubmission, SubmissionStatus
from app.models.class_ import Class
from app.models.exam import Exam, ExamResult, ExamStatus
from app.models.intervention import (
    Intervention,
    InterventionOutcome,
    InterventionStatus,
    InterventionType,
)
from app.models.meeting import MeetingRequest, MeetingStatus, MeetingType
from app.models.school import School
from app.models.student import Student, StudentStatus
from app.models.timetable import DayOfWeek, TimetableSlot
from app.models.user import User, UserRole, UserStatus
from app.services.risk_service import RiskService
from app.services.monthly_report_service import MonthlyReportService

# Fix random seed for reproducible, deterministic benchmark data
random.seed(42)

# ---------------------------------------------------------------------------
# Batch Writer Helper for High Performance Firestore Writes
# ---------------------------------------------------------------------------

class FirestoreBatchWriter:
    """Helper that buffers and automatically commits Firestore batch operations."""

    def __init__(self, db, batch_size: int = 400):
        self.db = db
        self.batch_size = batch_size
        self.batch = db.batch()
        self.count = 0
        self.total_committed = 0

    def set(self, doc_ref, data: Dict[str, Any]):
        self.batch.set(doc_ref, data)
        self.count += 1
        if self.count >= self.batch_size:
            self.commit()

    def commit(self):
        if self.count > 0:
            self.batch.commit()
            self.total_committed += self.count
            self.batch = self.db.batch()
            self.count = 0

    def flush(self):
        self.commit()
        return self.total_committed


# ---------------------------------------------------------------------------
# Name Lists & Generators
# ---------------------------------------------------------------------------

FIRST_NAMES_MALE = [
    "Aarav", "Advait", "Arjun", "Dev", "Dhruv", "Ishaan", "Kabir", "Manav",
    "Pranav", "Rahul", "Rohan", "Samar", "Shaurya", "Siddharth", "Tanmay",
    "Utkarsh", "Varun", "Vikram", "Vivaan", "Yash", "Aditya", "Akash",
    "Aniket", "Ayush", "Harsh", "Karan", "Kunal", "Nikhil", "Parth", "Rishi",
]

FIRST_NAMES_FEMALE = [
    "Aanya", "Aditi", "Ananya", "Anushka", "Avani", "Diya", "Isha", "Kavya",
    "Khushi", "Meera", "Myra", "Navya", "Pari", "Pooja", "Priya", "Rhea",
    "Riya", "Saanvi", "Sara", "Shreya", "Sneha", "Tanvi", "Tara", "Trisha",
    "Vanshika", "Vidhi", "Zara", "Simran", "Nandini", "Shruti",
]

LAST_NAMES = [
    "Agarwal", "Bose", "Chawla", "Chopra", "Das", "Deshmukh", "Dube", "Gupta",
    "Iyer", "Jain", "Joshi", "Kapoor", "Khan", "Kumar", "Malhotra", "Mehta",
    "Mishra", "Mukherjee", "Nair", "Patel", "Prasad", "Rao", "Reddy", "Roy",
    "Saxena", "Sen", "Sharma", "Singh", "Srivastava", "Verma",
]

TEACHER_NAMES = [
    ("Sarah", "Jenkins", "Mathematics"),
    ("Rajesh", "Sharma", "Physics"),
    ("Meenakshi", "Sundaram", "Chemistry"),
    ("Amit", "Verma", "Biology"),
    ("Pooja", "Bose", "English"),
    ("Sunil", "Gupta", "Mathematics"),
    ("Kavita", "Deshmukh", "Social Studies"),
    ("Vikram", "Sen", "Computer Science"),
    ("Deepa", "Nair", "Hindi"),
    ("Sanjay", "Malhotra", "Science"),
    ("Anita", "Roy", "English"),
    ("Rakesh", "Joshi", "Mathematics"),
    ("Geeta", "Agarwal", "Social Studies"),
    ("Manoj", "Chawla", "Physics"),
    ("Sneha", "Patel", "Chemistry"),
    ("Alok", "Mishra", "Biology"),
    ("Preeti", "Srivastava", "Hindi"),
    ("Tarun", "Kapoor", "Computer Science"),
    ("Neelam", "Saxena", "Science"),
    ("Harish", "Iyer", "Mathematics"),
    ("Swati", "Chopra", "English"),
    ("Gaurav", "Das", "Social Studies"),
    ("Divya", "Prasad", "Science"),
    ("Nitin", "Jain", "Computer Science"),
    ("Rashmi", "Reddy", "Hindi"),
    ("Anand", "Rao", "Physics"),
    ("Bhavna", "Khan", "Chemistry"),
    ("Chetan", "Mehta", "Biology"),
    ("Damini", "Singh", "English"),
    ("Eshwar", "Dube", "Mathematics"),
    ("Farida", "Mukherjee", "Social Studies"),
    ("Girish", "Kumar", "Science"),
    ("Hema", "Chawla", "Hindi"),
    ("Inder", "Joshi", "Computer Science"),
    ("Jaspreet", "Kaur", "English"),
]

SUBJECTS_BY_GRADE = {
    "junior": ["Mathematics", "Science", "English", "Social Studies", "Hindi", "Computer Science"],
    "senior": ["Mathematics", "Physics", "Chemistry", "Biology", "English", "Computer Science"],
}

# ---------------------------------------------------------------------------
# Date Range Helper (50 School Days = 10 Weeks)
# ---------------------------------------------------------------------------

def generate_school_days(num_weeks: int = 26, end_date: Optional[date] = None) -> List[str]:
    """Generates a list of weekday dates (YYYY-MM-DD) for 6 months (Apr-Sep 2026)."""
    if end_date is None:
        end_date = date(2026, 9, 30)
    
    # Adjust end_date to previous Friday if weekend
    while end_date.weekday() >= 5:
        end_date -= timedelta(days=1)

    days = []
    curr = end_date
    while len(days) < (num_weeks * 5):
        if curr.weekday() < 5:  # Monday to Friday
            days.append(curr.isoformat())
        curr -= timedelta(days=1)

    days.reverse()
    return days


# ---------------------------------------------------------------------------
# Student Trajectory Simulation Functions
# ---------------------------------------------------------------------------

def get_student_trajectory(
    profile: str, day_idx: int, total_days: int
) -> Tuple[str, str, float]:
    """
    Returns (attendance_status, homework_status, test_score_pct) for a student profile on a given day index.
    
    Profiles:
      - 'SUDDEN_DROP': Baseline high (~96%), drops sharply in the last 20% of the period to ~35%.
      - 'GRADUAL_DECLINE': Starts high (95%), steadily drops across the period to ~65%.
      - 'STABLE_HIGH': Consistently 92–98% attendance, 90–98% homework, 80–95% test scores.
      - 'IMPROVING': Starts low (65–70%), steadily improves to 88–95%.
      - 'NATURALLY_LOW_STABLE': Consistently 68–72% attendance, ~60% homework, ~55% tests without decline.
      - 'TEMPORARY_DIP': Stable high, has a 2-week drop, then returns to stable high.
      - 'NEEDS_DATA': Only present for the last 2-3 days.
    """
    t = day_idx / max(1, total_days - 1)  # 0.0 (oldest) to 1.0 (most recent)

    if profile == "NEEDS_DATA":
        if day_idx < total_days - 3:
            return "EXCUSED", "COMPLETED", 75.0
        return "PRESENT", "COMPLETED", 78.0

    if profile == "SUDDEN_DROP":
        if t < 0.70:
            att_prob = 0.96
            hw_prob = 0.92
            test_base = 86.0
        else:
            att_prob = 0.35
            hw_prob = 0.45
            test_base = 48.0

    elif profile == "GRADUAL_DECLINE":
        att_prob = 0.95 - (0.35 * t)     # 95% -> 60%
        hw_prob = 0.92 - (0.38 * t)      # 92% -> 54%
        test_base = 88.0 - (35.0 * t)    # 88 -> 53

    elif profile == "IMPROVING":
        att_prob = 0.72 + (0.24 * t)     # 72% -> 96%
        hw_prob = 0.60 + (0.32 * t)      # 60% -> 92%
        test_base = 55.0 + (30.0 * t)    # 55 -> 85

    elif profile == "NATURALLY_LOW_STABLE":
        att_prob = 0.69 + (random.uniform(-0.03, 0.03))
        hw_prob = 0.62 + (random.uniform(-0.04, 0.04))
        test_base = 54.0 + (random.uniform(-3.0, 3.0))

    elif profile == "TEMPORARY_DIP":
        if 0.50 <= t <= 0.70:  # Temporary 2-week dip in middle
            att_prob = 0.60
            hw_prob = 0.55
            test_base = 62.0
        else:
            att_prob = 0.95
            hw_prob = 0.92
            test_base = 85.0

    else:  # STABLE_HIGH
        att_prob = 0.95 + random.uniform(-0.03, 0.03)
        hw_prob = 0.92 + random.uniform(-0.04, 0.04)
        test_base = 82.0 + random.uniform(-4.0, 8.0)

    # Determine Attendance Status
    r_att = random.random()
    if r_att < att_prob:
        att_status = "PRESENT"
    elif r_att < att_prob + 0.04:
        att_status = "LATE"
    elif r_att < att_prob + 0.06:
        att_status = "EXCUSED"
    else:
        att_status = "ABSENT"

    # Determine Homework Status
    r_hw = random.random()
    if r_hw < hw_prob:
        hw_status = "COMPLETED"
    elif r_hw < hw_prob + 0.08:
        hw_status = "LATE"
    else:
        hw_status = "NOT_COMPLETED"

    # Determine Test Score
    test_score = min(100.0, max(20.0, test_base + random.uniform(-4.0, 4.0)))
    return att_status, hw_status, round(test_score, 1)


# ---------------------------------------------------------------------------
# Core Seeding Function
# ---------------------------------------------------------------------------

def seed_demo_data(school_id: str = "school-001", reset_existing: bool = True) -> Dict[str, Any]:
    """Populates Firestore with complete benchmark demo school dataset."""
    settings = get_settings()
    # In live production with a real GCP Firebase project, guard against overwriting live data.
    # In demo mode (mock Firestore or demo project ID), allow in-memory/demo seeding.
    if settings.is_production and settings.FIREBASE_PROJECT_ID != "classpulse-demo" and "mock" not in settings.FIREBASE_PRIVATE_KEY:
        print("[!] ERROR: Demo data seeding is strictly disabled in live production Cloud Firestore.")
        raise RuntimeError("Demo data seeding refused: Production environment detected.")

    print("=" * 80)
    print(f"[*] ClassPulse Demo Data Seeding Engine: school_id='{school_id}'")
    print("=" * 80)

    initialise_firebase()
    db = get_firestore_client()
    writer = FirestoreBatchWriter(db, batch_size=400)

    counts = {
        "schools": 0,
        "classes": 0,
        "teachers": 0,
        "students": 0,
        "attendance_records": 0,
        "homework_records": 0,
        "exams": 0,
        "exam_results": 0,
        "timetable_slots": 0,
        "teacher_conflicts": 0,
        "class_conflicts": 0,
        "assignments": 0,
        "assignment_submissions": 0,
        "doubts": 0,
        "interventions": 0,
        "announcements": 0,
        "meeting_requests": 0,
    }


    # 1. School Setup
    print("\n[1/10] Seeding Demo School...")
    school = School(
        id=school_id,
        name="Delhi Public School - Demo Campus",
        code="DPS-DEMO",
        district="South Zone",
        state="Delhi",
        country="India",
        status="ACTIVE",
    )
    writer.set(db.collection("schools").document(school_id), school.to_firestore())
    counts["schools"] += 1

    # 2. Principal & Teacher Accounts
    print("[2/10] Seeding Principal and 35 Teacher Profiles...")
    
    # Principal
    principal_user = User(
        id="sadmin-uid-001",
        firebase_uid="sadmin-uid-001",
        email="principal@school-001.example.com",
        name="Dr. Evelyn Reed (Principal)",
        role=UserRole.SCHOOL_ADMIN,
        school_id=school_id,
        status=UserStatus.ACTIVE,
    )
    writer.set(db.collection("users").document("sadmin-uid-001"), principal_user.to_firestore())

    # Demo Student User profile
    demo_student_user = User(
        id="student-uid-001",
        firebase_uid="student-uid-001",
        email="student001@school-001.example.com",
        name="Rahul Sharma (Student)",
        role=UserRole.STUDENT,
        school_id=school_id,
        status=UserStatus.ACTIVE,
    )
    writer.set(db.collection("users").document("student-uid-001"), demo_student_user.to_firestore())

    # Teacher Accounts
    teacher_ids = []
    teacher_users: Dict[str, User] = {}
    for i, (fn, ln, subj) in enumerate(TEACHER_NAMES):
        t_id = "teacher-uid-001" if i == 0 else f"teacher-uid-{i+1:03d}"
        email = "teacher@school-001.example.com" if i == 0 else f"teacher{i+1}@school-001.example.com"
        teacher_ids.append(t_id)

        t_user = User(
            id=t_id,
            firebase_uid=t_id,
            email=email,
            name=f"{fn} {ln}",
            role=UserRole.TEACHER,
            school_id=school_id,
            status=UserStatus.ACTIVE,
            subjects=[subj],
            assigned_classes=[],
        )
        teacher_users[t_id] = t_user
        writer.set(db.collection("users").document(t_id), t_user.to_firestore())
        counts["teachers"] += 1

    # 3. Classes (Grades 6 to 12, Sections A and B = 14 Classes)
    print("[3/10] Seeding 14 Classes (Grades 6 to 12, Sections A & B)...")
    grades = ["6", "7", "8", "9", "10", "11", "12"]
    sections = ["A", "B"]
    classes_list: List[Class] = []
    
    teacher_idx = 0
    for grade in grades:
        for sec in sections:
            cid = f"class-{grade}{sec.lower()}"
            c_teachers = [teacher_ids[teacher_idx % len(teacher_ids)], teacher_ids[(teacher_idx + 1) % len(teacher_ids)]]
            # Ensure teacher-uid-001 is assigned to class-10a
            if cid == "class-10a" and "teacher-uid-001" not in c_teachers:
                c_teachers.insert(0, "teacher-uid-001")

            c_obj = Class(
                id=cid,
                school_id=school_id,
                name=f"Grade {grade}-{sec}",
                grade=grade,
                section=sec,
                academic_year="2024-25",
                teacher_ids=c_teachers,
                status="ACTIVE",
            )
            classes_list.append(c_obj)
            writer.set(db.collection("classes").document(cid), c_obj.to_firestore())
            counts["classes"] += 1
            teacher_idx += 2

    # 4. Students & Longitudinal Records
    print("[4/12] Generating ~630 Students with 6-Month Academic Longitudinal Records...")
    school_days = generate_school_days(num_weeks=26, end_date=date(2026, 9, 30))
    total_days = len(school_days)  # ~130 days

    all_students: List[Student] = []
    student_profiles_map: Dict[str, str] = {}

    student_counter = 100

    for cls in classes_list:
        # Determine number of students per class (40 to 48 students)
        num_students = 45

        for roll in range(1, num_students + 1):
            student_counter += 1
            stu_id = f"stu-{student_counter}"
            stu_code = f"DPS-{cls.grade}{cls.section}-{roll:02d}"

            # Assign synthetic scenario profiles for Class 10-A
            if cls.id == "class-10a":
                if roll == 1:
                    profile = "SUDDEN_DROP"
                    name = "Rahul Sharma"
                    stu_id = "demo-student-001"  # Matches mock student token
                elif roll == 2:
                    profile = "GRADUAL_DECLINE"
                    name = "Priya Nair"
                    stu_id = "stu-102"
                elif roll == 3:
                    profile = "STABLE_HIGH"
                    name = "Aarav Patel"
                    stu_id = "stu-103"
                elif roll == 4:
                    profile = "IMPROVING"
                    name = "Ananya Roy"
                    stu_id = "stu-104"
                elif roll == 5:
                    profile = "NATURALLY_LOW_STABLE"
                    name = "Vikram Malhotra"
                    stu_id = "stu-105"
                elif roll == 6:
                    profile = "TEMPORARY_DIP"
                    name = "Rohan Verma"
                    stu_id = "stu-106"
                elif roll == 7:
                    profile = "NEEDS_DATA"
                    name = "Meera Joshi"
                    stu_id = "stu-107"
                else:
                    # Realistic distribution
                    r_prof = random.random()
                    if r_prof < 0.65:
                        profile = "STABLE_HIGH"
                    elif r_prof < 0.77:
                        profile = "IMPROVING"
                    elif r_prof < 0.89:
                        profile = "GRADUAL_DECLINE"
                    elif r_prof < 0.95:
                        profile = "NATURALLY_LOW_STABLE"
                    else:
                        profile = "SUDDEN_DROP"
                    fn = random.choice(FIRST_NAMES_MALE if roll % 2 == 0 else FIRST_NAMES_FEMALE)
                    ln = random.choice(LAST_NAMES)
                    name = f"{fn} {ln}"
            else:
                # Distribution for all other classes
                r_prof = random.random()
                if r_prof < 0.65:
                    profile = "STABLE_HIGH"
                elif r_prof < 0.77:
                    profile = "IMPROVING"
                elif r_prof < 0.89:
                    profile = "GRADUAL_DECLINE"
                elif r_prof < 0.95:
                    profile = "NATURALLY_LOW_STABLE"
                elif r_prof < 0.98:
                    profile = "SUDDEN_DROP"
                else:
                    profile = "NEEDS_DATA"
                fn = random.choice(FIRST_NAMES_MALE if roll % 2 == 0 else FIRST_NAMES_FEMALE)
                ln = random.choice(LAST_NAMES)
                name = f"{fn} {ln}"

            parent_phone = f"+91 98765 {random.randint(10000, 99999)}"
            
            student = Student(
                id=stu_id,
                school_id=school_id,
                class_id=cls.id,
                student_code=stu_code,
                name=name,
                grade=cls.grade,
                section=cls.section,
                parent_contact=parent_phone,
                status=StudentStatus.ACTIVE,
            )
            writer.set(db.collection("students").document(stu_id), student.to_firestore())
            all_students.append(student)
            student_profiles_map[stu_id] = profile
            counts["students"] += 1

            # Generate 50 daily attendance records for this student
            for d_idx, day_str in enumerate(school_days):
                att_status, _, _ = get_student_trajectory(profile, d_idx, total_days)
                att_id = AttendanceRecord.make_id(stu_id, day_str)
                att_rec = AttendanceRecord(
                    id=att_id,
                    student_id=stu_id,
                    school_id=school_id,
                    class_id=cls.id,
                    date=day_str,
                    status=AttendanceStatus(att_status),
                    source="csv",
                )
                writer.set(
                    db.collection("students").document(stu_id).collection("attendance").document(att_id),
                    att_rec.to_firestore(),
                )
                counts["attendance_records"] += 1

            # Generate 26 weekly homework records for this student
            for w_idx in range(26):
                hw_date = school_days[min(len(school_days) - 1, w_idx * 5 + 2)]  # Wednesday of each week
                hw_id_str = f"HW-W{w_idx+1:02d}"
                _, hw_status, _ = get_student_trajectory(profile, w_idx * 5, total_days)
                hw_rec_id = HomeworkRecord.make_id(stu_id, hw_id_str, hw_date)
                hw_rec = HomeworkRecord(
                    id=hw_rec_id,
                    student_id=stu_id,
                    school_id=school_id,
                    class_id=cls.id,
                    assignment_id=hw_id_str,
                    assignment_date=hw_date,
                    status=HomeworkStatus(hw_status),
                    source="csv",
                )
                writer.set(
                    db.collection("students").document(stu_id).collection("homework").document(hw_rec_id),
                    hw_rec.to_firestore(),
                )
                counts["homework_records"] += 1

    # Commit student and record batches
    writer.commit()

    # 5. Exams & Marks
    print("[5/12] Seeding Exams, Marks Entry & Longitudinal Test Scores across 6 Months...")
    exam_templates = [
        ("Unit Test 1", "Mathematics", school_days[min(len(school_days) - 1, 15)], 50.0),    # ~Late April
        ("Periodic Test 1", "Science", school_days[min(len(school_days) - 1, 38)], 50.0),     # ~Late May
        ("Mid-Term Exam", "Mathematics", school_days[min(len(school_days) - 1, 62)], 100.0), # ~Late June
        ("Periodic Test 2", "Social Studies", school_days[min(len(school_days) - 1, 85)], 50.0), # ~Late July
        ("Unit Test 2", "Science", school_days[min(len(school_days) - 1, 108)], 50.0),       # ~Late August
        ("Term Exam", "English", school_days[min(len(school_days) - 1, 126)], 100.0),        # ~Late September
    ]

    for cls in classes_list:
        cls_students = [s for s in all_students if s.class_id == cls.id]
        
        for e_idx, (e_name, subj, e_date, max_m) in enumerate(exam_templates):
            exam_id = f"exam-{cls.id}-{e_idx+1}"
            exam = Exam(
                id=exam_id,
                school_id=school_id,
                class_id=cls.id,
                teacher_id=cls.teacher_ids[0] if cls.teacher_ids else "teacher-uid-001",
                exam_name=f"{cls.name} {e_name}",
                subject=subj,
                exam_date=e_date,
                max_marks=max_m,
                status=ExamStatus.COMPLETED,
            )
            writer.set(db.collection("exams").document(exam_id), exam.to_firestore())
            counts["exams"] += 1

            for stu in cls_students:
                prof = student_profiles_map.get(stu.id, "STABLE_HIGH")
                day_offset = [15, 38, 62, 85, 108, 126][e_idx]
                _, _, score_pct = get_student_trajectory(prof, day_offset, total_days)
                obtained = round((score_pct / 100.0) * max_m, 1)
                obtained = min(max_m, max(0.0, obtained))

                # 1. ExamResult in exams/{id}/results/{res_id}
                res_id = ExamResult.make_id(exam_id, stu.id)
                e_res = ExamResult(
                    id=res_id,
                    exam_id=exam_id,
                    school_id=school_id,
                    class_id=cls.id,
                    student_id=stu.id,
                    obtained_marks=obtained,
                    max_marks=max_m,
                )
                writer.set(
                    db.collection("exams").document(exam_id).collection("results").document(res_id),
                    e_res.to_firestore(),
                )
                counts["exam_results"] += 1

                # 2. TestScoreRecord in students/{id}/test_scores/{t_id} (used by ML engine)
                t_score_id = TestScoreRecord.make_id(stu.id, subj, e_name, e_date)
                t_rec = TestScoreRecord(
                    id=t_score_id,
                    student_id=stu.id,
                    school_id=school_id,
                    class_id=cls.id,
                    subject=subj,
                    assessment_name=e_name,
                    assessment_date=e_date,
                    score=obtained,
                    max_score=max_m,
                    source="csv",
                )
                writer.set(
                    db.collection("students").document(stu.id).collection("test_scores").document(t_score_id),
                    t_rec.to_firestore(),
                )

    writer.commit()

    # 6. Interventions
    print("[6/10] Seeding Remedial and Preventative Interventions...")
    sample_interventions = [
        (
            "demo-student-001", "class-10a", InterventionType.PARENT_CONTACT,
            "Called mother regarding sharp attendance drop and missing midterm test. Scheduled follow-up counseling session.",
            "2024-09-02", InterventionStatus.IN_PROGRESS, None, None,
        ),
        (
            "demo-student-001", "class-10a", InterventionType.ACADEMIC_SUPPORT,
            "Enrolled student into Peer-Tutoring math remedial sessions on Tuesdays and Thursdays.",
            "2024-09-15", InterventionStatus.PLANNED, None, None,
        ),
        (
            "stu-102", "class-10a", InterventionType.ONE_ON_ONE_SUPPORT,
            "Conducted 1-on-1 check-in on steady grade decline. Student identified gaps in geometry basics.",
            "2024-08-20", InterventionStatus.COMPLETED, InterventionOutcome.STUDENT_IMPROVED, "Student attended 3 review sessions; recent quiz showed positive recovery.",
        ),
        (
            "stu-105", "class-10a", InterventionType.COUNSELING_REFERRAL,
            "Routine learning support check-in. Student confirmed stable baseline and no external stress.",
            "2024-08-28", InterventionStatus.COMPLETED, InterventionOutcome.STUDENT_UNCHANGED, "Baseline remains stable; no additional intervention required.",
        ),
    ]

    for stu_id, cid, itype, notes, f_date, istatus, outcome, outcome_notes in sample_interventions:
        int_id = str(uuid.uuid4())
        int_obj = Intervention(
            id=int_id,
            school_id=school_id,
            student_id=stu_id,
            teacher_id="teacher-uid-001",
            class_id=cid,
            type=itype,
            notes=notes,
            follow_up_date=f_date,
            status=istatus,
            outcome=outcome,
            outcome_notes=outcome_notes,
            created_at=datetime.now(tz=timezone.utc) - timedelta(days=7),
            updated_at=datetime.now(tz=timezone.utc),
        )
        writer.set(db.collection("interventions").document(int_id), int_obj.to_firestore())
        counts["interventions"] += 1

    # 7. Announcements
    print("[7/10] Seeding Targeted School Announcements...")
    announcements_data = [
        (
            "Annual Sports Day Registration Open",
            "Registrations for track & field, basketball, and badminton for the Annual Sports Meet 2024 are now live on the student portal. Submit nominations before Friday.",
            AnnouncementTarget.ALL_SCHOOL, None, None,
        ),
        (
            "Parent-Teacher Meeting Schedule (Term 1)",
            "The Term 1 Parent-Teacher Meeting will be held on Saturday from 8:30 AM to 1:30 PM. Parents can schedule priority slots with class teachers through the portal.",
            AnnouncementTarget.ALL_SCHOOL, None, None,
        ),
        (
            "Faculty Review Meeting - Wednesday 3:30 PM",
            "All department heads and classroom teachers are requested to attend the mid-term curriculum review meeting in Conference Room B.",
            AnnouncementTarget.TEACHERS, None, None,
        ),
        (
            "Mathematics Olympiad Final Submissions",
            "Students registered for the National Math Olympiad must collect their hall tickets and practice materials from the Math Department.",
            AnnouncementTarget.STUDENTS, None, None,
        ),
        (
            "Class 10-A Science Project Submission Deadline",
            "All Class 10-A students must submit their Physics laboratory experiment reports and models by Wednesday morning.",
            AnnouncementTarget.CLASS, "class-10a", None,
        ),
    ]

    for title, msg, target, target_cid, exp in announcements_data:
        ann_id = str(uuid.uuid4())
        ann = Announcement(
            id=ann_id,
            school_id=school_id,
            created_by="sadmin-uid-001",
            created_by_name="Dr. Evelyn Reed (Principal)",
            title=title,
            message=msg,
            target=target,
            target_class_id=target_cid,
            expires_at=exp,
        )
        writer.set(db.collection("announcements").document(ann_id), ann.to_firestore())
        counts["announcements"] += 1

    # 8. Meeting Requests
    print("[8/10] Seeding Appointment and Meeting Requests...")
    meetings_data = [
        (
            MeetingType.STUDENT_TEACHER,
            "student-uid-001", "Rahul Sharma",
            "teacher-uid-001", "Ms. Sarah Jenkins",
            "Clarification on Trigonometry Homework",
            "Dear Ms. Jenkins, I had difficulty with problems 14 to 18 on the assignment. Could we meet for 15 minutes?",
            school_days[-3], "14:30", MeetingStatus.ACCEPTED,
        ),
        (
            MeetingType.TEACHER_STUDENT,
            "teacher-uid-001", "Ms. Sarah Jenkins",
            "stu-102", "Priya Nair",
            "Mid-Term Geometry Review Session",
            "Hi Priya, let's review your recent quiz questions together to help prepare for the upcoming assessment.",
            school_days[-1], "15:00", MeetingStatus.PENDING,
        ),
        (
            MeetingType.STUDENT_PRINCIPAL,
            "student-uid-001", "Rahul Sharma",
            "sadmin-uid-001", "Dr. Evelyn Reed (Principal)",
            "Student Council Environment Club Proposal",
            "Respected Principal, the Student Council has drafted a proposal for solar energy awareness week.",
            school_days[-2], "11:00", MeetingStatus.PENDING,
        ),
    ]

    for m_type, req_by, req_by_name, req_to, req_to_name, subj, msg, p_date, p_time, m_stat in meetings_data:
        m_id = str(uuid.uuid4())
        meeting = MeetingRequest(
            id=m_id,
            school_id=school_id,
            meeting_type=m_type,
            requested_by=req_by,
            requested_by_name=req_by_name,
            requested_to=req_to,
            requested_to_name=req_to_name,
            subject=subj,
            message=msg,
            proposed_date=p_date,
            proposed_time=p_time,
            status=m_stat,
        )
        writer.set(db.collection("meeting_requests").document(m_id), meeting.to_firestore())
        counts["meeting_requests"] += 1

    # 9. Seeding Conflict-Free Weekly Timetables (Monday–Saturday, 6 Periods/Day)
    print("\n[9/10] Seeding Realistic Conflict-Free Weekly Timetables across all 14 Classes...")
    periods_def = [
        (1, "09:00", "09:50"),
        (2, "10:00", "10:50"),
        (3, "11:10", "12:00"),
        (4, "12:00", "12:50"),
        (5, "13:30", "14:20"),
        (6, "14:20", "15:10"),
    ]
    days_def = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]

    junior_subjects = ["Mathematics", "Science", "English", "Social Studies", "Hindi", "Computer Science"]
    senior_subjects = ["Mathematics", "Physics", "Chemistry", "Biology", "English", "Computer Science"]

    # Group teachers by qualified subject
    teachers_by_subject: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    for i, (fn, ln, subj) in enumerate(TEACHER_NAMES):
        t_id = "teacher-uid-001" if i == 0 else f"teacher-uid-{i+1:03d}"
        teachers_by_subject[subj].append((t_id, f"{fn} {ln}"))

    # Global tracking: (day, period) -> set of busy teacher IDs (school-wide)
    school_teacher_busy: Dict[Tuple[str, int], Set[str]] = defaultdict(set)
    # Track assigned classes per teacher
    teacher_assigned_classes: Dict[str, Set[str]] = defaultdict(set)

    # Anchor teachers for key demo classes (Class 10-A, 9-A)
    anchor_teachers_10a = {
        "Mathematics": ("teacher-uid-001", "Sarah Jenkins"),
        "Physics": ("teacher-uid-002", "Rajesh Sharma"),
        "Chemistry": ("teacher-uid-003", "Meenakshi Sundaram"),
        "Biology": ("teacher-uid-004", "Amit Verma"),
        "English": ("teacher-uid-005", "Pooja Bose"),
        "Computer Science": ("teacher-uid-008", "Vikram Sen"),
    }

    all_timetable_slots: List[TimetableSlot] = []

    for k, cls in enumerate(classes_list):
        grade_num = int(cls.grade)
        subjects = junior_subjects if grade_num <= 8 else senior_subjects

        for d_idx, day_str in enumerate(days_def):
            for p_idx, (p_num, start_time, end_time) in enumerate(periods_def):
                # Stagger subject schedule across classes and days to prevent collisions
                subj_idx = (p_idx + k + d_idx) % 6
                subject = subjects[subj_idx]

                # Pick teacher
                chosen_t_id = None
                chosen_t_name = None

                # For Class 10-A, use anchor teachers whenever available
                if cls.id == "class-10a" and subject in anchor_teachers_10a:
                    t_cand_id, t_cand_name = anchor_teachers_10a[subject]
                    if t_cand_id not in school_teacher_busy[(day_str, p_num)]:
                        chosen_t_id, chosen_t_name = t_cand_id, t_cand_name

                # Otherwise, find a free teacher qualified in this subject
                if not chosen_t_id:
                    cand_list = teachers_by_subject.get(subject, [])
                    for t_cand_id, t_cand_name in cand_list:
                        if t_cand_id not in school_teacher_busy[(day_str, p_num)]:
                            chosen_t_id, chosen_t_name = t_cand_id, t_cand_name
                            break

                # Fail-safe: if all teachers in subject are busy, pick ANY free teacher in school
                if not chosen_t_id:
                    for i, (fn, ln, s_alt) in enumerate(TEACHER_NAMES):
                        alt_id = "teacher-uid-001" if i == 0 else f"teacher-uid-{i+1:03d}"
                        if alt_id not in school_teacher_busy[(day_str, p_num)]:
                            chosen_t_id, chosen_t_name = alt_id, f"{fn} {ln}"
                            break

                if not chosen_t_id:
                    chosen_t_id = "teacher-uid-001"
                    chosen_t_name = "Sarah Jenkins"

                # Record in busy tracking
                school_teacher_busy[(day_str, p_num)].add(chosen_t_id)
                teacher_assigned_classes[chosen_t_id].add(cls.name)

                slot_id = f"slot-{school_id}-{cls.id}-{day_str.lower()}-p{p_num}"
                slot_obj = TimetableSlot(
                    id=slot_id,
                    school_id=school_id,
                    class_id=cls.id,
                    day_of_week=DayOfWeek(day_str),
                    period_number=p_num,
                    subject=subject,
                    teacher_id=chosen_t_id,
                    teacher_name=chosen_t_name,
                    start_time=start_time,
                    end_time=end_time,
                )
                writer.set(db.collection("timetables").document(slot_id), slot_obj.to_firestore())
                counts["timetable_slots"] += 1
                all_timetable_slots.append(slot_obj)

    # Update teacher documents in Firestore with their populated assigned_classes
    for t_id, t_user_obj in teacher_users.items():
        classes_set = teacher_assigned_classes.get(t_id, set())
        t_user_obj.assigned_classes = sorted(list(classes_set))
        writer.set(db.collection("users").document(t_id), t_user_obj.to_firestore())

    # Strict Scheduling Validation Check
    teacher_slots_check = defaultdict(list)
    class_slots_check = defaultdict(list)
    t_conflicts = 0
    c_conflicts = 0

    for slot in all_timetable_slots:
        assert slot.start_time < slot.end_time, f"Invalid time range in slot {slot.id}: {slot.start_time} >= {slot.end_time}"
        assert 1 <= slot.period_number <= 6, f"Invalid period number: {slot.period_number}"
        
        t_key = (slot.teacher_id, slot.day_of_week.value, slot.period_number)
        if t_key in teacher_slots_check:
            t_conflicts += 1
        teacher_slots_check[t_key].append(slot)

        c_key = (slot.class_id, slot.day_of_week.value, slot.period_number)
        if c_key in class_slots_check:
            c_conflicts += 1
        class_slots_check[c_key].append(slot)

    counts["teacher_conflicts"] = t_conflicts
    counts["class_conflicts"] = c_conflicts
    assert t_conflicts == 0, f"Critical: {t_conflicts} teacher conflicts found!"
    assert c_conflicts == 0, f"Critical: {c_conflicts} class conflicts found!"

    # Flush all remaining writes
    writer.flush()

    # 10. Seeding Realistic Classwork & Assignments across Classes
    print("\n[10/11] Seeding Realistic Classwork & Assignments across Classes...")
    today_dt = date.today()

    assignment_templates = [
        # Class 6-A
        {
            "class_id": "class-6a",
            "teacher_id": "teacher-uid-001",
            "teacher_name": "Sarah Jenkins",
            "title": "Fractions & Decimals Operations",
            "subject": "Mathematics",
            "description": "Complete word problems 1 to 15 on converting improper fractions to mixed numbers and decimal addition.",
            "due_date": (today_dt + timedelta(days=3)).isoformat(),
            "due_time": "23:59",
            "max_marks": 20.0,
            "attachments": [
                {"title": "fractions_practice.pdf", "url": "https://example.com/fractions_practice.pdf", "file_type": "pdf"}
            ],
            "status": AssignmentStatus.PUBLISHED,
        },
        {
            "class_id": "class-6a",
            "teacher_id": "teacher-uid-002",
            "teacher_name": "Rajesh Sharma",
            "title": "Components of Food & Balanced Diet",
            "subject": "Science",
            "description": "Record a 3-day meal chart and categorize each item into carbohydrates, proteins, fats, vitamins, and roughage.",
            "due_date": (today_dt + timedelta(days=5)).isoformat(),
            "due_time": "18:00",
            "max_marks": 25.0,
            "attachments": [],
            "status": AssignmentStatus.PUBLISHED,
        },
        {
            "class_id": "class-6a",
            "teacher_id": "teacher-uid-005",
            "teacher_name": "Pooja Bose",
            "title": "Descriptive Paragraph: My Favorite Season",
            "subject": "English",
            "description": "Write a descriptive paragraph of 150-200 words focusing on sensory details and proper adjective usage.",
            "due_date": (today_dt - timedelta(days=2)).isoformat(),
            "due_time": "23:59",
            "max_marks": 15.0,
            "attachments": [],
            "status": AssignmentStatus.PUBLISHED,
        },
        # Class 10-A
        {
            "class_id": "class-10a",
            "teacher_id": "teacher-uid-001",
            "teacher_name": "Sarah Jenkins",
            "title": "Quadratic Equations Problem Set",
            "subject": "Mathematics",
            "description": "Complete exercises 4.1 to 4.3 from NCERT textbook. Show step-by-step factorization.",
            "due_date": (today_dt + timedelta(days=2)).isoformat(),
            "due_time": "23:59",
            "max_marks": 20.0,
            "attachments": [
                {"title": "algebra_questions.pdf", "url": "https://example.com/algebra_questions.pdf", "file_type": "pdf"}
            ],
            "status": AssignmentStatus.PUBLISHED,
        },
        {
            "class_id": "class-10a",
            "teacher_id": "teacher-uid-002",
            "teacher_name": "Rajesh Sharma",
            "title": "Optics & Ray Diagrams Worksheet",
            "subject": "Physics",
            "description": "Construct ray diagrams for concave mirror object positions at C, F, and between P & F.",
            "due_date": (today_dt + timedelta(days=4)).isoformat(),
            "due_time": "17:00",
            "max_marks": 25.0,
            "attachments": [
                {"title": "optics_guide.pdf", "url": "https://example.com/optics_guide.pdf", "file_type": "pdf"}
            ],
            "status": AssignmentStatus.PUBLISHED,
        },
        {
            "class_id": "class-10a",
            "teacher_id": "teacher-uid-005",
            "teacher_name": "Pooja Bose",
            "title": "Critical Essay: The Merchant of Venice",
            "subject": "English",
            "description": "Write a 500-word analytical essay discussing the trial scene and characterization of Portia.",
            "due_date": (today_dt + timedelta(days=7)).isoformat(),
            "due_time": "23:59",
            "max_marks": 20.0,
            "attachments": [],
            "status": AssignmentStatus.PUBLISHED,
        },
        {
            "class_id": "class-10a",
            "teacher_id": "teacher-uid-003",
            "teacher_name": "Anita Desai",
            "title": "Periodic Table Trends Summary",
            "subject": "Chemistry",
            "description": "Create a comparative table showing atomic radius, ionization enthalpy, and electronegativity trends across Period 3.",
            "due_date": (today_dt - timedelta(days=3)).isoformat(),
            "due_time": "23:59",
            "max_marks": 15.0,
            "attachments": [
                {"title": "periodic_trends.pdf", "url": "https://example.com/periodic_trends.pdf", "file_type": "pdf"}
            ],
            "status": AssignmentStatus.PUBLISHED,
        },
        # Class 10-B
        {
            "class_id": "class-10b",
            "teacher_id": "teacher-uid-001",
            "teacher_name": "Sarah Jenkins",
            "title": "Trigonometric Identities Practice",
            "subject": "Mathematics",
            "description": "Solve identities from worksheet sections A and B.",
            "due_date": (today_dt + timedelta(days=3)).isoformat(),
            "due_time": "23:59",
            "max_marks": 20.0,
            "attachments": [],
            "status": AssignmentStatus.PUBLISHED,
        },
        # Class 9-A
        {
            "class_id": "class-9a",
            "teacher_id": "teacher-uid-001",
            "teacher_name": "Sarah Jenkins",
            "title": "Polynomials Division Algorithm",
            "subject": "Mathematics",
            "description": "Verify remainder theorem for given cubic polynomials.",
            "due_date": (today_dt + timedelta(days=5)).isoformat(),
            "due_time": "23:59",
            "max_marks": 20.0,
            "attachments": [],
            "status": AssignmentStatus.PUBLISHED,
        },
    ]

    for a_idx, tmpl in enumerate(assignment_templates):
        assign_id = f"assign-{tmpl['class_id']}-{a_idx+1}"
        assign = Assignment(
            id=assign_id,
            school_id=school_id,
            class_id=tmpl["class_id"],
            teacher_id=tmpl["teacher_id"],
            teacher_name=tmpl["teacher_name"],
            title=tmpl["title"],
            subject=tmpl["subject"],
            description=tmpl["description"],
            due_date=tmpl["due_date"],
            due_time=tmpl["due_time"],
            max_marks=tmpl["max_marks"],
            attachments=tmpl["attachments"],
            status=tmpl["status"],
        )
        writer.set(db.collection("assignments").document(assign_id), assign.to_firestore())
        counts["assignments"] += 1

        cls_students = [s for s in all_students if s.class_id == tmpl["class_id"]]
        is_past = tmpl["due_date"] < today_dt.isoformat()

        for stu_idx, stu in enumerate(cls_students):
            prof = student_profiles_map.get(stu.id, "STABLE_HIGH")
            sub_id = AssignmentSubmission.make_id(assign_id, stu.id)

            should_submit = True
            is_late = False
            if is_past:
                if prof in ("SUDDEN_DROP", "GRADUAL_DECLINE") and stu_idx % 3 == 0:
                    should_submit = False
                elif stu_idx % 7 == 0:
                    is_late = True
            else:
                if stu_idx > 18:
                    should_submit = False
                elif stu_idx % 6 == 0:
                    is_late = False

            if should_submit:
                if is_past:
                    _, _, score_pct = get_student_trajectory(prof, 40, total_days)
                    obtained = round((score_pct / 100.0) * tmpl["max_marks"], 1)
                    obtained = min(tmpl["max_marks"], max(2.0, obtained))
                    sub = AssignmentSubmission(
                        id=sub_id,
                        assignment_id=assign_id,
                        school_id=school_id,
                        class_id=tmpl["class_id"],
                        student_id=stu.id,
                        student_name=stu.name,
                        student_code=stu.student_code,
                        submitted_at=datetime.now(tz=timezone.utc) - timedelta(days=4),
                        content="Attached complete working and answers for review.",
                        attachment_name="submission_file.pdf",
                        attachment_url="https://example.com/submission.pdf",
                        status=SubmissionStatus.GRADED,
                        is_late=is_late,
                        obtained_marks=obtained,
                        feedback="Solid understanding demonstrated. Neat presentation." if obtained >= 12 else "Review steps carefully for problem 3.",
                        graded_by=tmpl["teacher_id"],
                        graded_at=datetime.now(tz=timezone.utc) - timedelta(days=2),
                    )
                else:
                    sub = AssignmentSubmission(
                        id=sub_id,
                        assignment_id=assign_id,
                        school_id=school_id,
                        class_id=tmpl["class_id"],
                        student_id=stu.id,
                        student_name=stu.name,
                        student_code=stu.student_code,
                        submitted_at=datetime.now(tz=timezone.utc) - timedelta(hours=stu_idx + 1),
                        content="Here are my answers for the assignment.",
                        attachment_name="answers_scan.pdf",
                        attachment_url="https://example.com/answers.pdf",
                        status=SubmissionStatus.SUBMITTED,
                        is_late=False,
                    )

                writer.set(
                    db.collection("assignments").document(assign_id).collection("submissions").document(sub_id),
                    sub.to_firestore(),
                )
                counts["assignment_submissions"] += 1

    # Flush assignments writes
    writer.flush()

    # 10b. Seed Realistic Academic Doubts (Phase 5C)
    print("\n[10b/12] Seeding Realistic Academic Doubts...")
    from app.models.doubt import Doubt, DoubtReply, DoubtStatus, DoubtVisibility
    import uuid as _uuid_doubt

    _doubt_templates = [
        # Class 6-A Doubts
        {
            "class_id": "class-6a", "student_idx": 0,
            "title": "How to convert an improper fraction to a mixed fraction?",
            "body": "When solving 17/5, how do we write it as a mixed fraction? Is 3 2/5 correct?",
            "subject": "Mathematics", "status": DoubtStatus.ANSWERED,
            "reply_body": "Yes, exactly! Divide 17 by 5: Quotient = 3, Remainder = 2, Divisor = 5. So it is 3 2/5 (Three and two-fifths).",
            "teacher_id": "teacher-uid-001", "teacher_name": "Ms. Sarah Jenkins",
        },
        {
            "class_id": "class-6a", "student_idx": 1,
            "title": "Why do desert plants have spines instead of leaves?",
            "body": "Does the spine help the plant perform photosynthesis, or is it only for protection?",
            "subject": "Science", "status": DoubtStatus.ANSWERED,
            "reply_body": "Spines reduce water loss through transpiration because they have minimal surface area! In cactus plants, the green fleshy stem takes over photosynthesis.",
            "teacher_id": "teacher-uid-002", "teacher_name": "Mr. Rajesh Sharma",
        },
        {
            "class_id": "class-6a", "student_idx": 2,
            "title": "Difference between transitive and intransitive verbs?",
            "body": "Can a sentence have an intransitive verb and still have a prepositional phrase following it?",
            "subject": "English", "status": DoubtStatus.OPEN,
            "reply_body": None, "teacher_id": None, "teacher_name": None,
        },
        # Class 10-A Doubts
        {
            "class_id": "class-10a", "student_idx": 0,
            "title": "Integration by parts: when to apply it?",
            "body": "I understand the formula but am unsure when to choose integration by parts over substitution. Example please?",
            "subject": "Mathematics", "status": DoubtStatus.ANSWERED,
            "reply_body": "Use LIATE rule: L=Log, I=Inverse trig, A=Algebraic, T=Trig, E=Exponential. Choose u as whichever comes first. Example: for x.cos(x)dx, u=x, dv=cos(x)dx.",
            "teacher_id": "teacher-uid-001", "teacher_name": "Ms. Sarah Jenkins",
        },
        {
            "class_id": "class-10a", "student_idx": 1,
            "title": "Why does concave mirror form a real image?",
            "body": "How does a concave mirror always form a real image when the object is beyond the focus?",
            "subject": "Physics", "status": DoubtStatus.ANSWERED,
            "reply_body": "Beyond focus, reflected rays actually converge (meet) on the same side as the object ? making it a real image projectable on a screen.",
            "teacher_id": "teacher-uid-002", "teacher_name": "Mr. Rajesh Sharma",
        },
        {
            "class_id": "class-10a", "student_idx": 2,
            "title": "Difference between ionic and covalent bonds?",
            "body": "I keep confusing ionic and covalent bonds. Is there a simple way to remember?",
            "subject": "Chemistry", "status": DoubtStatus.OPEN,
            "reply_body": None, "teacher_id": None, "teacher_name": None,
        },
        {
            "class_id": "class-10a", "student_idx": 3,
            "title": "Can DNA be repaired by the body?",
            "body": "Our Bio chapter says cells can repair DNA. What types of damage can be repaired and what leads to cancer?",
            "subject": "Biology", "status": DoubtStatus.ANSWERED,
            "reply_body": "Yes! Single-strand breaks use the intact strand as template. Double-strand breaks use Homologous Recombination (accurate) or NHEJ (error-prone). When repair fails, mutations accumulate and may lead to cancer.",
            "teacher_id": "teacher-uid-003", "teacher_name": "Ms. Priya Nair",
        },
        {
            "class_id": "class-10a", "student_idx": 4,
            "title": "Portia mercy speech literary devices?",
            "body": "List main literary devices in Portia mercy speech for the essay assignment.",
            "subject": "English", "status": DoubtStatus.ANSWERED,
            "reply_body": "Key devices: Metaphor (mercy=rain), Personification (mercy seasons justice), Anaphora (repeated It), Parallelism (sceptre vs mercy), Alliteration (Mightiest in the mightiest).",
            "teacher_id": "teacher-uid-005", "teacher_name": "Ms. Pooja Bose",
        },
        {
            "class_id": "class-10a", "student_idx": 5,
            "title": "How to distinguish HCl from H2SO4 in the lab?",
            "body": "What reagents or tests differentiate HCl and H2SO4 in practicals?",
            "subject": "Chemistry", "status": DoubtStatus.OPEN,
            "reply_body": None, "teacher_id": None, "teacher_name": None,
        },
    ]

    _doubt_count = 0
    for _tmpl in _doubt_templates:
        _cls_id = _tmpl["class_id"]
        _cls_stus = [s for s in all_students if s.class_id == _cls_id]
        if not _cls_stus:
            continue
        _stu = _cls_stus[_tmpl["student_idx"] % len(_cls_stus)]
        _did = str(_uuid_doubt.uuid4())
        _now = datetime.now(tz=timezone.utc)

        _doubt = Doubt(
            id=_did, school_id=school_id, class_id=_cls_id, subject=_tmpl["subject"],
            student_id=_stu.id, student_name=_stu.name,
            title=_tmpl["title"], body=_tmpl["body"],
            status=_tmpl["status"], visibility=DoubtVisibility.CLASS,
            reply_count=1 if _tmpl["reply_body"] else 0,
            views=random.randint(5, 35),
            answered_by=_tmpl.get("teacher_id"),
            answered_by_name=_tmpl.get("teacher_name"),
            answered_at=_now if _tmpl["status"] == DoubtStatus.ANSWERED else None,
            created_at=_now - timedelta(days=random.randint(1, 7)),
            updated_at=_now,
        )
        db.collection("doubts").document(_did).set(_doubt.to_firestore())
        _doubt_count += 1

        if _tmpl["reply_body"] and _tmpl["teacher_id"]:
            _rid = str(_uuid_doubt.uuid4())
            _reply = DoubtReply(
                id=_rid, doubt_id=_did, school_id=school_id, class_id=_cls_id,
                author_id=_tmpl["teacher_id"], author_name=_tmpl["teacher_name"],
                author_role="TEACHER", body=_tmpl["reply_body"],
                is_verified_answer=True,
                created_at=_now - timedelta(hours=random.randint(1, 20)),
                updated_at=_now,
            )
            db.collection("doubts").document(_did).collection("replies").document(_rid).set(_reply.to_firestore())

    print(f"  Seeded {_doubt_count} academic doubts")
    counts["doubts"] = _doubt_count

    # 11. Execute AI Risk Engine over all 14 classes
    print("\n[11/12] Executing AI Risk Engine across all 14 Class Cohorts...")

    total_alerts = 0
    for cls in classes_list:
        try:
            summary = RiskService.analyze_class_risk(cls.id, school_id)
            total_alerts += len(summary.alerts)
        except Exception as exc:
            print(f"  [!] Note: Cohort analysis for {cls.id}: {exc}")

    counts["risk_alerts"] = total_alerts

    # 12. Pre-generate Monthly Reports for 2026-04 through 2026-09
    print("\n[12/12] Pre-generating Monthly Reports & Historical Risk Analytics (2026-04 through 2026-09)...")
    monthly_report_periods = ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]
    total_monthly_reports = 0
    for m in monthly_report_periods:
        try:
            MonthlyReportService.generate_school_report(school_id, m, force=True)
            total_monthly_reports += 1
            print(f"  Generated complete cohort monthly reports for {m}")
        except Exception as exc:
            print(f"  [!] Note: Monthly report generation for {m}: {exc}")

    counts["monthly_report_periods"] = total_monthly_reports

    print("\n" + "=" * 80)
    print("                    SEEDING COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print(f"  Schools Created:           {counts['schools']}")
    print(f"  Classes Created:           {counts['classes']}")
    print(f"  Teachers Created:          {counts['teachers']}")
    print(f"  Students Enrolled:         {counts['students']}")
    print(f"  Attendance Records Logged: {counts['attendance_records']}")
    print(f"  Homework Records Logged:   {counts['homework_records']}")
    print(f"  Exams Scheduled:           {counts['exams']}")
    print(f"  Exam Results Recorded:     {counts['exam_results']}")
    print(f"  Timetable Slots Seeded:    {counts['timetable_slots']} (36 slots x 14 classes)")
    print(f"  Teacher Conflicts:         {counts['teacher_conflicts']}")
    print(f"  Class Conflicts:           {counts['class_conflicts']}")
    print(f"  Assignments Created:       {counts['assignments']}")
    print(f"  Submissions Logged:        {counts['assignment_submissions']}")
    print(f"  Active Risk Alerts:        {counts['risk_alerts']}")
    print(f"  Interventions Recorded:    {counts['interventions']}")
    print(f"  Announcements Published:   {counts['announcements']}")
    print(f"  Meeting Requests Logged:   {counts['meeting_requests']}")
    print("=" * 80)

    return counts


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ClassPulse Demo Data Populator")
    parser.add_argument("--school-id", default="school-001", help="Target School ID (default: school-001)")
    parser.add_argument("--reset", action="store_true", help="Safely reset demo school data prior to seeding")
    parser.add_argument("--seed", action="store_true", default=True, help="Seed demo school dataset")
    args = parser.parse_args()

    seed_demo_data(school_id=args.school_id, reset_existing=args.reset)


if __name__ == "__main__":
    main()
