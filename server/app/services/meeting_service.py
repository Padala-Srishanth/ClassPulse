"""
app.services.meeting_service — Meeting Request Service
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.core.firebase import get_firestore_client
from app.models.meeting import MeetingRequest, MeetingStatus, MeetingType


class MeetingService:

    @staticmethod
    def _col():
        return get_firestore_client().collection("meeting_requests")

    @classmethod
    def create_request(
        cls,
        school_id: str,
        meeting_type: MeetingType,
        requested_by: str,
        requested_by_name: str,
        requested_to: str,
        requested_to_name: str,
        subject: str,
        message: str,
        proposed_date: str,
        proposed_time: Optional[str] = None,
    ) -> MeetingRequest:
        req_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc)
        req = MeetingRequest(
            id=req_id,
            school_id=school_id,
            meeting_type=meeting_type,
            requested_by=requested_by,
            requested_by_name=requested_by_name,
            requested_to=requested_to,
            requested_to_name=requested_to_name,
            subject=subject,
            message=message,
            proposed_date=proposed_date,
            proposed_time=proposed_time,
            status=MeetingStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        cls._col().document(req_id).set(req.to_firestore())
        return req

    @classmethod
    def get_request(cls, req_id: str) -> Optional[MeetingRequest]:
        doc = cls._col().document(req_id).get()
        if not doc.exists:
            return None
        return MeetingRequest.from_firestore(doc.id, doc.to_dict())

    @classmethod
    def update_status(cls, req_id: str, status: MeetingStatus, response_note: Optional[str] = None) -> Optional[MeetingRequest]:
        req = cls.get_request(req_id)
        if not req:
            return None
        updates = {
            "status": status.value,
            "updated_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        if response_note is not None:
            updates["response_note"] = response_note
        cls._col().document(req_id).update(updates)
        req.status = status
        if response_note:
            req.response_note = response_note
        return req

    @classmethod
    def list_for_user(cls, uid: str, school_id: str) -> List[MeetingRequest]:
        """Get all meeting requests where user is either requester or target."""
        sent_docs = cls._col().where("requested_by", "==", uid).where("school_id", "==", school_id).stream()
        recv_docs = cls._col().where("requested_to", "==", uid).where("school_id", "==", school_id).stream()
        seen = set()
        results = []
        for doc in list(sent_docs) + list(recv_docs):
            if doc.id not in seen:
                seen.add(doc.id)
                results.append(MeetingRequest.from_firestore(doc.id, doc.to_dict()))
        return sorted(results, key=lambda r: r.created_at, reverse=True)

    @classmethod
    def list_school_requests(cls, school_id: str) -> List[MeetingRequest]:
        docs = cls._col().where("school_id", "==", school_id).order_by("created_at").stream()
        return [MeetingRequest.from_firestore(d.id, d.to_dict()) for d in docs]
