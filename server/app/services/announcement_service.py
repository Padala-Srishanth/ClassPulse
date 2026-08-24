"""
app.services.announcement_service — Announcement Service
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.core.firebase import get_firestore_client
from app.models.announcement import Announcement, AnnouncementTarget


class AnnouncementService:

    @staticmethod
    def _col():
        return get_firestore_client().collection("announcements")

    @classmethod
    def create_announcement(
        cls,
        school_id: str,
        created_by: str,
        created_by_name: str,
        title: str,
        message: str,
        target: AnnouncementTarget,
        target_class_id: Optional[str] = None,
        expires_at: Optional[str] = None,
    ) -> Announcement:
        ann_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc)
        ann = Announcement(
            id=ann_id,
            school_id=school_id,
            created_by=created_by,
            created_by_name=created_by_name,
            title=title,
            message=message,
            target=target,
            target_class_id=target_class_id,
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
        )
        cls._col().document(ann_id).set(ann.to_firestore())
        return ann

    @classmethod
    def list_school_announcements(cls, school_id: str, limit: int = 50) -> List[Announcement]:
        docs = (
            cls._col()
            .where("school_id", "==", school_id)
            .order_by("created_at")
            .limit(limit)
            .stream()
        )
        return [Announcement.from_firestore(d.id, d.to_dict()) for d in docs]

    @classmethod
    def list_for_class(cls, school_id: str, class_id: str) -> List[Announcement]:
        """Get announcements visible to a specific class (school-wide + class-specific)."""
        docs = cls._col().where("school_id", "==", school_id).stream()
        results = []
        for d in docs:
            ann = Announcement.from_firestore(d.id, d.to_dict())
            if ann.target in (AnnouncementTarget.ALL_SCHOOL, AnnouncementTarget.STUDENTS):
                results.append(ann)
            elif ann.target in (AnnouncementTarget.CLASS, AnnouncementTarget.SECTION):
                if ann.target_class_id == class_id:
                    results.append(ann)
        return sorted(results, key=lambda a: a.created_at, reverse=True)

    @classmethod
    def list_for_students(cls, school_id: str, class_id: Optional[str] = None) -> List[Announcement]:
        """Get announcements visible to students (ALL_SCHOOL, STUDENTS, and matching class if provided)."""
        docs = cls._col().where("school_id", "==", school_id).stream()
        results = []
        for d in docs:
            ann = Announcement.from_firestore(d.id, d.to_dict())
            if ann.target in (AnnouncementTarget.ALL_SCHOOL, AnnouncementTarget.STUDENTS):
                results.append(ann)
            elif class_id and ann.target in (AnnouncementTarget.CLASS, AnnouncementTarget.SECTION) and ann.target_class_id == class_id:
                results.append(ann)
        return sorted(results, key=lambda a: a.created_at, reverse=True)

    @classmethod
    def list_for_teachers(cls, school_id: str) -> List[Announcement]:
        """Get announcements visible to teachers."""
        docs = (
            cls._col()
            .where("school_id", "==", school_id)
            .stream()
        )
        results = []
        for d in docs:
            ann = Announcement.from_firestore(d.id, d.to_dict())
            if ann.target in (AnnouncementTarget.ALL_SCHOOL, AnnouncementTarget.TEACHERS):
                results.append(ann)
        return sorted(results, key=lambda a: a.created_at, reverse=True)

