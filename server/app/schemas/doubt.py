"""
app.schemas.doubt - Pydantic Request/Response Schemas for Doubts
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DoubtCreate(BaseModel):
    class_id: Optional[str] = None
    subject: Optional[str] = None
    title: str
    body: str = ""
    attachment_name: Optional[str] = None
    attachment_url: Optional[str] = None
    visibility: str = "CLASS"


class DoubtUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    subject: Optional[str] = None
    status: Optional[str] = None
    visibility: Optional[str] = None


class DoubtReplyCreate(BaseModel):
    body: str
    attachment_name: Optional[str] = None
    attachment_url: Optional[str] = None


class DoubtResponse(BaseModel):
    id: str
    school_id: str
    class_id: str
    subject: Optional[str]
    student_id: str
    student_name: str
    title: str
    body: str
    attachment_name: Optional[str]
    attachment_url: Optional[str]
    status: str
    visibility: str
    reply_count: int
    views: int
    answered_by: Optional[str]
    answered_by_name: Optional[str]
    answered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, m) -> "DoubtResponse":
        return cls(**m.model_dump(mode="json"))


class DoubtReplyResponse(BaseModel):
    id: str
    doubt_id: str
    school_id: str
    class_id: str
    author_id: str
    author_name: str
    author_role: str
    body: str
    attachment_name: Optional[str]
    attachment_url: Optional[str]
    is_verified_answer: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, m) -> "DoubtReplyResponse":
        return cls(**m.model_dump(mode="json"))
