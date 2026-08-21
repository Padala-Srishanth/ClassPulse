"""
app.core.mock_firestore — In-Memory Firestore Engine & Demo Data Seeder
Provides local in-memory Firestore storage when Cloud Firestore API is disabled or running offline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional
import uuid


class MockDocumentSnapshot:
    def __init__(self, doc_id: str, data: Optional[Dict[str, Any]]):
        self.id = doc_id
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data) if self._data is not None else {}


class MockDocumentReference:
    def __init__(self, doc_id: str, store: Dict[str, Any], subcollections: Dict[str, Any]):
        self.id = doc_id
        self._store = store
        self._subcollections = subcollections

    def get(self) -> MockDocumentSnapshot:
        return MockDocumentSnapshot(self.id, self._store.get(self.id))

    def set(self, data: Dict[str, Any]):
        self._store[self.id] = dict(data)

    def update(self, data: Dict[str, Any]):
        if self.id in self._store:
            self._store[self.id].update(data)
        else:
            self._store[self.id] = dict(data)

    def collection(self, name: str) -> "MockCollectionReference":
        key = f"{self.id}/{name}"
        if key not in self._subcollections:
            self._subcollections[key] = {}
        return MockCollectionReference(self._subcollections[key], self._subcollections)


class MockQuery:
    def __init__(self, store: Dict[str, Any], subcollections: Dict[str, Any], filters=None, order_field=None, offset_val=0, limit_val=None):
        self._store = store
        self._subcollections = subcollections
        self._filters = filters or []
        self._order_field = order_field
        self._offset_val = offset_val
        self._limit_val = limit_val

    def where(self, field: str, op: str, value: Any) -> "MockQuery":
        new_filters = list(self._filters)
        new_filters.append((field, op, value))
        return MockQuery(self._store, self._subcollections, new_filters, self._order_field, self._offset_val, self._limit_val)

    def order_by(self, field: str) -> "MockQuery":
        return MockQuery(self._store, self._subcollections, self._filters, field, self._offset_val, self._limit_val)

    def offset(self, val: int) -> "MockQuery":
        return MockQuery(self._store, self._subcollections, self._filters, self._order_field, val, self._limit_val)

    def limit(self, val: int) -> "MockQuery":
        return MockQuery(self._store, self._subcollections, self._filters, self._order_field, self._offset_val, val)

    def stream(self) -> Generator[MockDocumentSnapshot, None, None]:
        items = list(self._store.items())
        
        filtered = []
        for doc_id, doc_data in items:
            match = True
            for field, op, val in self._filters:
                if op == "==":
                    if doc_data.get(field) != val:
                        match = False
                        break
            if match:
                filtered.append((doc_id, doc_data))

        if self._order_field:
            filtered.sort(key=lambda x: str(x[1].get(self._order_field, "")))

        if self._offset_val:
            filtered = filtered[self._offset_val:]
        if self._limit_val is not None:
            filtered = filtered[:self._limit_val]

        for doc_id, doc_data in filtered:
            yield MockDocumentSnapshot(doc_id, doc_data)


class MockCollectionReference(MockQuery):
    def __init__(self, store: Dict[str, Any], subcollections: Dict[str, Any]):
        super().__init__(store, subcollections)

    def document(self, doc_id: str) -> MockDocumentReference:
        return MockDocumentReference(doc_id, self._store, self._subcollections)


class MockBatch:
    def __init__(self, root_db: "MockFirestore"):
        self._ops = []
        self._root_db = root_db

    def set(self, doc_ref: MockDocumentReference, data: Dict[str, Any]):
        self._ops.append(("set", doc_ref, data))

    def commit(self):
        for op, doc_ref, data in self._ops:
            if op == "set":
                doc_ref.set(data)
        self._ops.clear()


class MockFirestore:
    def __init__(self):
        self._collections: Dict[str, Dict[str, Any]] = {}
        self._subcollections: Dict[str, Dict[str, Any]] = {}

    def collection(self, name: str) -> MockCollectionReference:
        if name not in self._collections:
            self._collections[name] = {}
        return MockCollectionReference(self._collections[name], self._subcollections)

    def collections(self):
        return iter([self.collection(k) for k in self._collections])

    def batch(self) -> MockBatch:
        return MockBatch(self)

    def clear(self):
        self._collections.clear()
        self._subcollections.clear()


# Global Singleton for local in-memory Firestore
_local_db_instance = MockFirestore()


def get_local_firestore() -> MockFirestore:
    return _local_db_instance


def seed_local_demo_data(db: MockFirestore):
    """Seed comprehensive demo cohort data in memory for instant local UI testability."""
    from app.models.academic import AttendanceRecord, HomeworkRecord, TestScoreRecord
    from app.models.class_ import Class
    from app.models.intervention import Intervention, InterventionStatus, InterventionType
    from app.models.school import School
    from app.models.student import Student
    from app.models.user import User, UserRole
    from app.services.risk_service import RiskService

    school_id = "school-001"
    class_id = "class-10a"

    # School
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

    # Users
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

    # Class
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

    # Students & Trajectories
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

        profile = s_info["profile"]

        def add_att(dates, status_list):
            for d, st in zip(dates, status_list):
                att_id = AttendanceRecord.make_id(s_id, d)
                rec = AttendanceRecord(id=att_id, student_id=s_id, school_id=school_id, class_id=class_id, date=d, status=st, source="csv")
                db.collection("students").document(s_id).collection("attendance").document(att_id).set(rec.to_firestore())

        def add_hw(assign_id, date, status):
            hw_id = HomeworkRecord.make_id(s_id, assign_id, date)
            rec = HomeworkRecord(id=hw_id, student_id=s_id, school_id=school_id, class_id=class_id, assignment_id=assign_id, assignment_date=date, status=status, source="csv")
            db.collection("students").document(s_id).collection("homework").document(hw_id).set(rec.to_firestore())

        def add_test(subject, name, date, score, max_score):
            t_id = TestScoreRecord.make_id(s_id, subject, name, date)
            rec = TestScoreRecord(id=t_id, student_id=s_id, school_id=school_id, class_id=class_id, subject=subject, assessment_name=name, assessment_date=date, score=score, max_score=max_score, percentage=round(score/max_score*100, 1), source="csv")
            db.collection("students").document(s_id).collection("test_scores").document(t_id).set(rec.to_firestore())

        if profile == "SHARP_DROP":
            add_att(dates_w1, ["PRESENT"] * 5)
            add_att(dates_w2, ["PRESENT"] * 5)
            add_att(dates_w3, ["ABSENT", "ABSENT", "PRESENT", "ABSENT", "ABSENT"])
            add_att(dates_w4, ["ABSENT", "ABSENT", "ABSENT", "ABSENT", "PRESENT"])

            add_hw("HW-01", "2024-07-24", "COMPLETED")
            add_hw("HW-02", "2024-07-31", "COMPLETED")
            add_hw("HW-03", "2024-08-07", "NOT_COMPLETED")
            add_hw("HW-04", "2024-08-14", "NOT_COMPLETED")


            add_test("Math", "Unit Test 1", "2024-07-26", 48, 50)
            add_test("Science", "Unit Test 1", "2024-08-02", 45, 50)
            add_test("Math", "Midterm Quiz", "2024-08-16", 18, 50)

        elif profile == "GRADUAL_DECLINE":
            add_att(dates_w1, ["PRESENT"] * 5)
            add_att(dates_w2, ["PRESENT", "PRESENT", "ABSENT", "PRESENT", "PRESENT"])
            add_att(dates_w3, ["PRESENT", "ABSENT", "PRESENT", "ABSENT", "PRESENT"])
            add_att(dates_w4, ["ABSENT", "PRESENT", "ABSENT", "PRESENT", "ABSENT"])

            add_hw("HW-01", "2024-07-24", "COMPLETED")
            add_hw("HW-02", "2024-07-31", "COMPLETED")
            add_hw("HW-03", "2024-08-07", "NOT_COMPLETED")
            add_hw("HW-04", "2024-08-14", "NOT_COMPLETED")


            add_test("English", "Unit 1", "2024-07-26", 42, 50)
            add_test("English", "Unit 2", "2024-08-16", 32, 50)

        else:
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

    # Initial AI Risk calculations
    RiskService.analyze_class_risk(class_id, school_id)



    # Sample Intervention
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
