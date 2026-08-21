"""
app.services.test_score_service — Test Score Service
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from app.core.firebase import get_firestore_client
from app.models.academic import TestScoreRecord
from app.schemas.academic import TestScoreCreate


class TestScoreService:
    @staticmethod
    def _subcollection(student_id: str):
        return get_firestore_client().collection("students").document(student_id).collection("test_scores")

    @classmethod
    def record_test_score(cls, data: TestScoreCreate, batch_id: Optional[str] = None) -> TestScoreRecord:
        record_id = TestScoreRecord.make_id(
            data.student_id, data.subject, data.assessment_name, data.assessment_date
        )
        now = datetime.now(tz=timezone.utc)
        
        record = TestScoreRecord(
            id=record_id,
            student_id=data.student_id,
            school_id=data.school_id,
            class_id=data.class_id,
            subject=data.subject,
            assessment_name=data.assessment_name,
            assessment_date=data.assessment_date,
            score=data.score,
            max_score=data.max_score,
            source=data.source,
            import_batch_id=batch_id,
            created_at=now,
        )
        
        cls._subcollection(data.student_id).document(record_id).set(record.to_firestore())
        return record

    @classmethod
    def list_student_test_scores(cls, student_id: str, skip: int = 0, limit: int = 50) -> List[TestScoreRecord]:
        docs = cls._subcollection(student_id).order_by("assessment_date").offset(skip).limit(limit).stream()
        return [TestScoreRecord.from_firestore(doc.id, doc.to_dict()) for doc in docs]
