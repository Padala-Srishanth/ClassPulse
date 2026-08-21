"""
app.services.intervention_service — Intervention Management Service
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from app.core.firebase import get_firestore_client
from app.models.intervention import (
    Intervention,
    InterventionOutcome,
    InterventionStatus,
    InterventionType,
)
from app.schemas.intervention import InterventionCreate, InterventionUpdate


class InterventionService:
    @staticmethod
    def _collection():
        return get_firestore_client().collection("interventions")

    @classmethod
    def create_intervention(cls, data: InterventionCreate, teacher_id: str) -> Intervention:
        db = cls._collection()
        intervention_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc)

        intervention = Intervention(
            id=intervention_id,
            school_id=data.school_id,
            student_id=data.student_id,
            teacher_id=teacher_id,
            class_id=data.class_id,
            type=data.type,
            notes=data.notes,
            follow_up_date=data.follow_up_date,
            status=InterventionStatus.PLANNED,
            created_at=now,
            updated_at=now,
        )

        db.document(intervention_id).set(intervention.to_firestore())
        return intervention

    @classmethod
    def get_intervention(cls, intervention_id: str) -> Optional[Intervention]:
        doc = cls._collection().document(intervention_id).get()
        if not doc.exists:
            return None
        return Intervention.from_firestore(doc.id, doc.to_dict())

    @classmethod
    def update_intervention(
        cls, intervention_id: str, data: InterventionUpdate
    ) -> Optional[Intervention]:
        doc_ref = cls._collection().document(intervention_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None

        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not updates:
            return Intervention.from_firestore(doc.id, doc.to_dict())

        updates["updated_at"] = datetime.now(tz=timezone.utc)
        if "type" in updates and isinstance(updates["type"], InterventionType):
            updates["type"] = updates["type"].value
        if "status" in updates and isinstance(updates["status"], InterventionStatus):
            updates["status"] = updates["status"].value
        if "outcome" in updates and isinstance(updates["outcome"], InterventionOutcome):
            updates["outcome"] = updates["outcome"].value

        doc_ref.update(updates)
        updated_doc = doc_ref.get()
        return Intervention.from_firestore(updated_doc.id, updated_doc.to_dict())

    @classmethod
    def list_student_interventions(
        cls, student_id: str, skip: int = 0, limit: int = 50
    ) -> List[Intervention]:
        docs = (
            cls._collection()
            .where("student_id", "==", student_id)
            .offset(skip)
            .limit(limit)
            .stream()
        )
        return [Intervention.from_firestore(doc.id, doc.to_dict()) for doc in docs]

    @classmethod
    def list_class_interventions(
        cls, class_id: str, skip: int = 0, limit: int = 50
    ) -> List[Intervention]:
        docs = (
            cls._collection()
            .where("class_id", "==", class_id)
            .offset(skip)
            .limit(limit)
            .stream()
        )
        return [Intervention.from_firestore(doc.id, doc.to_dict()) for doc in docs]

    @classmethod
    def list_school_interventions(
        cls, school_id: str, skip: int = 0, limit: int = 50
    ) -> List[Intervention]:
        docs = (
            cls._collection()
            .where("school_id", "==", school_id)
            .offset(skip)
            .limit(limit)
            .stream()
        )
        return [Intervention.from_firestore(doc.id, doc.to_dict()) for doc in docs]
