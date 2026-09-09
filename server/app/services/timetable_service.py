"""
app.services.timetable_service — Timetable Management Service
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.core.firebase import get_firestore_client
from app.models.timetable import DAY_ORDER, TimetableSlot
from app.schemas.timetable import TimetableSlotCreate, TimetableSlotUpdate


class TimetableService:

    @staticmethod
    def _col():
        return get_firestore_client().collection("timetables")

    @classmethod
    def create_slot(cls, data: TimetableSlotCreate) -> TimetableSlot:
        # Validate time order
        data.validate_time_order()

        slot_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc)
        slot = TimetableSlot(
            id=slot_id,
            school_id=data.school_id,
            class_id=data.class_id,
            day_of_week=data.day_of_week,
            period_number=data.period_number,
            subject=data.subject,
            teacher_id=data.teacher_id,
            teacher_name=data.teacher_name,
            start_time=data.start_time,
            end_time=data.end_time,
            created_at=now,
            updated_at=now,
        )
        cls._col().document(slot_id).set(slot.to_firestore())
        return slot

    @classmethod
    def get_slot(cls, slot_id: str) -> Optional[TimetableSlot]:
        doc = cls._col().document(slot_id).get()
        if not doc.exists:
            return None
        return TimetableSlot.from_firestore(doc.id, doc.to_dict())

    @classmethod
    def list_class_slots(cls, class_id: str) -> List[TimetableSlot]:
        """Return all timetable slots for a class, sorted by day + period."""
        docs = (
            cls._col()
            .where("class_id", "==", class_id)
            .stream()
        )
        slots = [TimetableSlot.from_firestore(d.id, d.to_dict()) for d in docs]
        # Sort by day order then period number
        slots.sort(key=lambda s: (DAY_ORDER.get(s.day_of_week.value, 99), s.period_number))
        return slots

    @classmethod
    def list_teacher_slots(cls, teacher_id: str) -> List[TimetableSlot]:
        """Return all slots where this teacher is assigned."""
        docs = (
            cls._col()
            .where("teacher_id", "==", teacher_id)
            .stream()
        )
        slots = [TimetableSlot.from_firestore(d.id, d.to_dict()) for d in docs]
        slots.sort(key=lambda s: (DAY_ORDER.get(s.day_of_week.value, 99), s.period_number))
        return slots

    @classmethod
    def list_school_slots(cls, school_id: str) -> List[TimetableSlot]:
        """Return all timetable slots for a school."""
        docs = (
            cls._col()
            .where("school_id", "==", school_id)
            .stream()
        )
        slots = [TimetableSlot.from_firestore(d.id, d.to_dict()) for d in docs]
        slots.sort(key=lambda s: (s.class_id, DAY_ORDER.get(s.day_of_week.value, 99), s.period_number))
        return slots

    @classmethod
    def update_slot(cls, slot_id: str, data: TimetableSlotUpdate) -> Optional[TimetableSlot]:
        doc_ref = cls._col().document(slot_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None

        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not updates:
            return TimetableSlot.from_firestore(doc.id, doc.to_dict())

        # Validate time order if both times present
        existing = TimetableSlot.from_firestore(doc.id, doc.to_dict())
        new_start = updates.get("start_time", existing.start_time)
        new_end = updates.get("end_time", existing.end_time)
        if new_start >= new_end:
            raise ValueError(f"start_time ({new_start}) must be before end_time ({new_end})")

        if "day_of_week" in updates:
            from app.models.timetable import DayOfWeek
            updates["day_of_week"] = DayOfWeek(updates["day_of_week"]).value

        updates["updated_at"] = datetime.now(tz=timezone.utc)
        doc_ref.update(updates)
        updated = doc_ref.get()
        return TimetableSlot.from_firestore(updated.id, updated.to_dict())

    @classmethod
    def delete_slot(cls, slot_id: str) -> bool:
        doc_ref = cls._col().document(slot_id)
        if not doc_ref.get().exists:
            return False
        doc_ref.delete()
        return True
