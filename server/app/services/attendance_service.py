"""
app.services.attendance_service — Attendance Service
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from app.core.firebase import get_firestore_client
from app.models.academic import AttendanceRecord
from app.schemas.academic import AttendanceCreate


class AttendanceService:
    @staticmethod
    def _subcollection(student_id: str):
        return get_firestore_client().collection("students").document(student_id).collection("attendance")

    @classmethod
    def record_attendance(cls, data: AttendanceCreate, batch_id: Optional[str] = None) -> AttendanceRecord:
        record_id = AttendanceRecord.make_id(data.student_id, data.date)
        now = datetime.now(tz=timezone.utc)
        
        record = AttendanceRecord(
            id=record_id,
            student_id=data.student_id,
            school_id=data.school_id,
            class_id=data.class_id,
            date=data.date,
            status=data.status,
            source=data.source,
            import_batch_id=batch_id,
            created_at=now,
        )
        
        cls._subcollection(data.student_id).document(record_id).set(record.to_firestore())
        return record

    @classmethod
    def list_student_attendance(cls, student_id: str, skip: int = 0, limit: int = 50) -> List[AttendanceRecord]:
        docs = cls._subcollection(student_id).order_by("date").offset(skip).limit(limit).stream()
        return [AttendanceRecord.from_firestore(doc.id, doc.to_dict()) for doc in docs]
