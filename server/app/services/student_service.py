"""
app.services.student_service — Student Management Service
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from app.core.firebase import get_firestore_client
from app.models.student import Student, StudentStatus
from app.schemas.student import StudentCreate, StudentUpdate


class StudentService:
    @staticmethod
    def _collection():
        return get_firestore_client().collection("students")

    @classmethod
    def create_student(cls, data: StudentCreate) -> Student:
        db = cls._collection()
        student_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc)
        
        student = Student(
            id=student_id,
            school_id=data.school_id,
            class_id=data.class_id,
            student_code=data.student_code,
            name=data.name,
            grade=data.grade,
            section=data.section,
            status=StudentStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        
        db.document(student_id).set(student.to_firestore())
        return student

    @classmethod
    def get_student(cls, student_id: str) -> Optional[Student]:
        doc = cls._collection().document(student_id).get()
        if not doc.exists:
            return None
        return Student.from_firestore(doc.id, doc.to_dict())

    @classmethod
    def get_student_by_code(cls, school_id: str, student_code: str) -> Optional[Student]:
        query = (
            cls._collection()
            .where("school_id", "==", school_id)
            .where("student_code", "==", student_code)
            .limit(1)
        )
        docs = list(query.stream())
        if not docs:
            return None
        return Student.from_firestore(docs[0].id, docs[0].to_dict())

    @classmethod
    def update_student(cls, student_id: str, data: StudentUpdate) -> Optional[Student]:
        doc_ref = cls._collection().document(student_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None
        
        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not updates:
            return Student.from_firestore(doc.id, doc.to_dict())
            
        updates["updated_at"] = datetime.now(tz=timezone.utc)
        if "status" in updates and isinstance(updates["status"], StudentStatus):
            updates["status"] = updates["status"].value

        doc_ref.update(updates)
        updated_doc = doc_ref.get()
        return Student.from_firestore(updated_doc.id, updated_doc.to_dict())

    @classmethod
    def list_class_students(cls, class_id: str, skip: int = 0, limit: int = 50) -> List[Student]:
        query = cls._collection().where("class_id", "==", class_id).offset(skip).limit(limit)
        docs = query.stream()
        return [Student.from_firestore(doc.id, doc.to_dict()) for doc in docs]
