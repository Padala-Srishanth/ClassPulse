"""
app.services.school_service — School Management Service
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from app.core.firebase import get_firestore_client
from app.models.school import School, SchoolStatus
from app.schemas.school import SchoolCreate, SchoolUpdate


class SchoolService:
    @staticmethod
    def _collection():
        return get_firestore_client().collection("schools")

    @classmethod
    def create_school(cls, data: SchoolCreate) -> School:
        db = cls._collection()
        school_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc)
        
        school = School(
            id=school_id,
            name=data.name,
            code=data.code,
            district=data.district,
            state=data.state,
            country=data.country,
            status=SchoolStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        
        db.document(school_id).set(school.to_firestore())
        return school

    @classmethod
    def get_school(cls, school_id: str) -> Optional[School]:
        doc = cls._collection().document(school_id).get()
        if not doc.exists:
            return None
        return School.from_firestore(doc.id, doc.to_dict())

    @classmethod
    def update_school(cls, school_id: str, data: SchoolUpdate) -> Optional[School]:
        doc_ref = cls._collection().document(school_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None
        
        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not updates:
            return School.from_firestore(doc.id, doc.to_dict())
            
        updates["updated_at"] = datetime.now(tz=timezone.utc)
        if "status" in updates and isinstance(updates["status"], SchoolStatus):
            updates["status"] = updates["status"].value

        doc_ref.update(updates)
        updated_doc = doc_ref.get()
        return School.from_firestore(updated_doc.id, updated_doc.to_dict())

    @classmethod
    def list_schools(cls, skip: int = 0, limit: int = 50) -> List[School]:
        docs = cls._collection().offset(skip).limit(limit).stream()
        return [School.from_firestore(doc.id, doc.to_dict()) for doc in docs]
