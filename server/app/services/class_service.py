"""
app.services.class_service — Class Management Service
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from app.core.firebase import get_firestore_client
from app.models.class_ import Class, ClassStatus
from app.schemas.class_ import ClassCreate, ClassUpdate


class ClassService:
    @staticmethod
    def _collection():
        return get_firestore_client().collection("classes")

    @classmethod
    def create_class(cls, data: ClassCreate) -> Class:
        db = cls._collection()
        class_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc)
        
        class_obj = Class(
            id=class_id,
            school_id=data.school_id,
            name=data.name,
            grade=data.grade,
            section=data.section,
            academic_year=data.academic_year,
            teacher_ids=data.teacher_ids,
            status=ClassStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        
        db.document(class_id).set(class_obj.to_firestore())
        return class_obj

    @classmethod
    def get_class(cls, class_id: str) -> Optional[Class]:
        doc = cls._collection().document(class_id).get()
        if not doc.exists:
            return None
        return Class.from_firestore(doc.id, doc.to_dict())

    @classmethod
    def update_class(cls, class_id: str, data: ClassUpdate) -> Optional[Class]:
        doc_ref = cls._collection().document(class_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None
        
        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not updates:
            return Class.from_firestore(doc.id, doc.to_dict())
            
        updates["updated_at"] = datetime.now(tz=timezone.utc)
        if "status" in updates and isinstance(updates["status"], ClassStatus):
            updates["status"] = updates["status"].value

        doc_ref.update(updates)
        updated_doc = doc_ref.get()
        return Class.from_firestore(updated_doc.id, updated_doc.to_dict())

    @classmethod
    def list_school_classes(cls, school_id: str, skip: int = 0, limit: int = 50) -> List[Class]:
        query = cls._collection().where("school_id", "==", school_id).offset(skip).limit(limit)
        docs = query.stream()
        return [Class.from_firestore(doc.id, doc.to_dict()) for doc in docs]
