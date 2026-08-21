"""
app.services.homework_service — Homework Service
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from app.core.firebase import get_firestore_client
from app.models.academic import HomeworkRecord
from app.schemas.academic import HomeworkCreate


class HomeworkService:
    @staticmethod
    def _subcollection(student_id: str):
        return get_firestore_client().collection("students").document(student_id).collection("homework")

    @classmethod
    def record_homework(cls, data: HomeworkCreate, batch_id: Optional[str] = None) -> HomeworkRecord:
        record_id = HomeworkRecord.make_id(data.student_id, data.assignment_id, data.assignment_date)
        now = datetime.now(tz=timezone.utc)
        
        record = HomeworkRecord(
            id=record_id,
            student_id=data.student_id,
            school_id=data.school_id,
            class_id=data.class_id,
            assignment_id=data.assignment_id,
            assignment_date=data.assignment_date,
            status=data.status,
            source=data.source,
            import_batch_id=batch_id,
            created_at=now,
        )
        
        cls._subcollection(data.student_id).document(record_id).set(record.to_firestore())
        return record

    @classmethod
    def list_student_homework(cls, student_id: str, skip: int = 0, limit: int = 50) -> List[HomeworkRecord]:
        docs = cls._subcollection(student_id).order_by("assignment_date").offset(skip).limit(limit).stream()
        return [HomeworkRecord.from_firestore(doc.id, doc.to_dict()) for doc in docs]
