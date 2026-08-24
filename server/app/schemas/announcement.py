"""
app.schemas.announcement — Announcement API Schemas
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from app.models.announcement import AnnouncementTarget


class AnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)
    target: AnnouncementTarget
    target_class_id: Optional[str] = None
    expires_at: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class AnnouncementResponse(BaseModel):
    id: str
    school_id: str
    created_by: str
    created_by_name: str
    title: str
    message: str
    target: str
    target_class_id: Optional[str]
    expires_at: Optional[str]
    created_at: str

    @classmethod
    def from_model(cls, ann) -> "AnnouncementResponse":
        return cls(
            id=ann.id,
            school_id=ann.school_id,
            created_by=ann.created_by,
            created_by_name=ann.created_by_name,
            title=ann.title,
            message=ann.message,
            target=ann.target.value,
            target_class_id=ann.target_class_id,
            expires_at=ann.expires_at,
            created_at=ann.created_at.isoformat(),
        )
