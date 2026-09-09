"""
app.models.doubt - Doubt and DoubtReply Domain Models
"""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DoubtStatus(str, Enum):
    OPEN = "OPEN"
    ANSWERED = "ANSWERED"
    CLOSED = "CLOSED"


class DoubtVisibility(str, Enum):
    CLASS = "CLASS"
    PRIVATE = "PRIVATE"


class Doubt(BaseModel):
    id: str
    school_id: str
    class_id: str
    subject: Optional[str] = None
    student_id: str
    student_name: str
    title: str
    body: str = ""
    attachment_name: Optional[str] = None
    attachment_url: Optional[str] = None
    status: DoubtStatus = DoubtStatus.OPEN
    visibility: DoubtVisibility = DoubtVisibility.CLASS
    reply_count: int = 0
    views: int = 0
    answered_by: Optional[str] = None
    answered_by_name: Optional[str] = None
    answered_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict):
        data = dict(data)
        data["id"] = doc_id
        for f in ("created_at", "updated_at", "answered_at"):
            if f in data and data[f] and hasattr(data[f], "timestamp"):
                from datetime import datetime as dt
                data[f] = dt.fromtimestamp(data[f].timestamp(), tz=timezone.utc)
        return cls(**data)

    def to_firestore(self) -> dict:
        d = self.model_dump(exclude={"id"}, mode="json")
        d["status"] = self.status.value
        d["visibility"] = self.visibility.value
        return d


class DoubtReply(BaseModel):
    id: str
    doubt_id: str
    school_id: str
    class_id: str
    author_id: str
    author_name: str
    author_role: str
    body: str
    attachment_name: Optional[str] = None
    attachment_url: Optional[str] = None
    is_verified_answer: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict):
        data = dict(data)
        data["id"] = doc_id
        for f in ("created_at", "updated_at"):
            if f in data and data[f] and hasattr(data[f], "timestamp"):
                from datetime import datetime as dt
                data[f] = dt.fromtimestamp(data[f].timestamp(), tz=timezone.utc)
        return cls(**data)

    def to_firestore(self) -> dict:
        return self.model_dump(exclude={"id"}, mode="json")
