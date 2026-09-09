"""
app.services.doubt_service - Doubt Discussion Business Logic
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.core.firebase import get_firestore_client
from app.models.doubt import Doubt, DoubtReply, DoubtStatus, DoubtVisibility
from app.services.student_service import StudentService


class DoubtService:

    @staticmethod
    def _doubts_col():
        return get_firestore_client().collection("doubts")

    @staticmethod
    def _replies_col(doubt_id: str):
        return get_firestore_client().collection("doubts").document(doubt_id).collection("replies")

    # ------------------------------------------------------------------
    # Doubt CRUD
    # ------------------------------------------------------------------

    @classmethod
    def create_doubt(
        cls,
        school_id: str,
        class_id: str,
        student_id: str,
        student_name: str,
        title: str,
        body: str = "",
        subject: Optional[str] = None,
        attachment_name: Optional[str] = None,
        attachment_url: Optional[str] = None,
        visibility: DoubtVisibility = DoubtVisibility.CLASS,
    ) -> Doubt:
        doubt_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc)
        doubt = Doubt(
            id=doubt_id,
            school_id=school_id,
            class_id=class_id,
            subject=subject,
            student_id=student_id,
            student_name=student_name,
            title=title,
            body=body,
            attachment_name=attachment_name,
            attachment_url=attachment_url,
            visibility=visibility,
            status=DoubtStatus.OPEN,
            reply_count=0,
            views=0,
            created_at=now,
            updated_at=now,
        )
        cls._doubts_col().document(doubt_id).set(doubt.to_firestore())
        return doubt

    @classmethod
    def get_doubt(cls, doubt_id: str) -> Optional[Doubt]:
        doc = cls._doubts_col().document(doubt_id).get()
        if not doc.exists:
            return None
        return Doubt.from_firestore(doc.id, doc.to_dict())

    @classmethod
    def update_doubt(cls, doubt_id: str, updates: dict) -> Optional[Doubt]:
        doc_ref = cls._doubts_col().document(doubt_id)
        if not doc_ref.get().exists:
            return None
        clean = {k: v for k, v in updates.items() if v is not None}
        clean["updated_at"] = datetime.now(tz=timezone.utc).isoformat()
        doc_ref.update(clean)
        return cls.get_doubt(doubt_id)

    @classmethod
    def delete_doubt(cls, doubt_id: str) -> bool:
        doc_ref = cls._doubts_col().document(doubt_id)
        if not doc_ref.get().exists:
            return False
        # Delete replies
        for rd in cls._replies_col(doubt_id).stream():
            rd.reference.delete()
        doc_ref.delete()
        return True

    @classmethod
    def list_class_doubts(
        cls,
        class_id: str,
        subject: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Doubt]:
        q = cls._doubts_col().where("class_id", "==", class_id)
        if subject:
            q = q.where("subject", "==", subject)
        if status:
            q = q.where("status", "==", status)
        docs = q.limit(limit).stream()
        doubts = [Doubt.from_firestore(d.id, d.to_dict()) for d in docs]
        doubts.sort(key=lambda d: d.created_at, reverse=True)
        return doubts

    @classmethod
    def list_student_doubts(cls, student_id: str, school_id: str) -> List[Doubt]:
        docs = (
            cls._doubts_col()
            .where("school_id", "==", school_id)
            .where("student_id", "==", student_id)
            .stream()
        )
        doubts = [Doubt.from_firestore(d.id, d.to_dict()) for d in docs]
        doubts.sort(key=lambda d: d.created_at, reverse=True)
        return doubts

    @classmethod
    def list_school_doubts(cls, school_id: str, status: Optional[str] = None, limit: int = 200) -> List[Doubt]:
        q = cls._doubts_col().where("school_id", "==", school_id)
        if status:
            q = q.where("status", "==", status)
        docs = q.limit(limit).stream()
        doubts = [Doubt.from_firestore(d.id, d.to_dict()) for d in docs]
        doubts.sort(key=lambda d: d.created_at, reverse=True)
        return doubts

    @classmethod
    def increment_views(cls, doubt_id: str) -> None:
        doc_ref = cls._doubts_col().document(doubt_id)
        try:
            from google.cloud.firestore_v1 import transforms
            doc_ref.update({"views": transforms.SERVER_TIMESTAMP})
        except Exception:
            pass  # Non-critical - best effort

    # ------------------------------------------------------------------
    # Replies
    # ------------------------------------------------------------------

    @classmethod
    def add_reply(
        cls,
        doubt_id: str,
        school_id: str,
        class_id: str,
        author_id: str,
        author_name: str,
        author_role: str,
        body: str,
        attachment_name: Optional[str] = None,
        attachment_url: Optional[str] = None,
    ) -> DoubtReply:
        reply_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc)
        reply = DoubtReply(
            id=reply_id,
            doubt_id=doubt_id,
            school_id=school_id,
            class_id=class_id,
            author_id=author_id,
            author_name=author_name,
            author_role=author_role,
            body=body,
            attachment_name=attachment_name,
            attachment_url=attachment_url,
            is_verified_answer=False,
            created_at=now,
            updated_at=now,
        )
        cls._replies_col(doubt_id).document(reply_id).set(reply.to_firestore())

        # Increment reply_count on parent doubt
        doubt_ref = cls._doubts_col().document(doubt_id)
        doubt_doc = doubt_ref.get()
        if doubt_doc.exists:
            current = doubt_doc.to_dict().get("reply_count", 0)
            doubt_ref.update({
                "reply_count": current + 1,
                "updated_at": now.isoformat(),
            })

        return reply

    @classmethod
    def list_replies(cls, doubt_id: str) -> List[DoubtReply]:
        docs = cls._replies_col(doubt_id).stream()
        replies = [DoubtReply.from_firestore(d.id, d.to_dict()) for d in docs]
        replies.sort(key=lambda r: r.created_at)
        return replies

    @classmethod
    def delete_reply(cls, doubt_id: str, reply_id: str) -> bool:
        ref = cls._replies_col(doubt_id).document(reply_id)
        if not ref.get().exists:
            return False
        ref.delete()
        # Decrement reply count
        doubt_ref = cls._doubts_col().document(doubt_id)
        doubt_doc = doubt_ref.get()
        if doubt_doc.exists:
            current = max(0, doubt_doc.to_dict().get("reply_count", 1) - 1)
            doubt_ref.update({"reply_count": current})
        return True

    @classmethod
    def mark_as_answered(
        cls,
        doubt_id: str,
        reply_id: str,
        teacher_uid: str,
        teacher_name: str,
    ) -> Optional[Doubt]:
        """Mark a specific reply as the verified answer and close the doubt."""
        # Mark reply as verified
        reply_ref = cls._replies_col(doubt_id).document(reply_id)
        reply_doc = reply_ref.get()
        if not reply_doc.exists:
            return None
        now = datetime.now(tz=timezone.utc)
        reply_ref.update({"is_verified_answer": True, "updated_at": now.isoformat()})

        # Update doubt status
        cls._doubts_col().document(doubt_id).update({
            "status": DoubtStatus.ANSWERED.value,
            "answered_by": teacher_uid,
            "answered_by_name": teacher_name,
            "answered_at": now.isoformat(),
            "updated_at": now.isoformat(),
        })
        return cls.get_doubt(doubt_id)

    @classmethod
    def close_doubt(cls, doubt_id: str) -> Optional[Doubt]:
        now = datetime.now(tz=timezone.utc)
        cls._doubts_col().document(doubt_id).update({
            "status": DoubtStatus.CLOSED.value,
            "updated_at": now.isoformat(),
        })
        return cls.get_doubt(doubt_id)

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    @classmethod
    def get_school_doubt_stats(cls, school_id: str) -> dict:
        all_doubts = cls.list_school_doubts(school_id)
        total = len(all_doubts)
        open_count = sum(1 for d in all_doubts if d.status == DoubtStatus.OPEN)
        answered = sum(1 for d in all_doubts if d.status == DoubtStatus.ANSWERED)
        closed = sum(1 for d in all_doubts if d.status == DoubtStatus.CLOSED)

        # Group by subject
        subject_counts: dict = {}
        for d in all_doubts:
            s = d.subject or "General"
            subject_counts[s] = subject_counts.get(s, 0) + 1

        answer_rate = round(answered / total * 100, 1) if total > 0 else 0.0

        return {
            "total": total,
            "open": open_count,
            "answered": answered,
            "closed": closed,
            "answer_rate": answer_rate,
            "by_subject": subject_counts,
        }
