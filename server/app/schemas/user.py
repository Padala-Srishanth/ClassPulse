"""
app.schemas.user — User API Request/Response Schemas
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.core.security import UserRole
from app.models.user import UserStatus


class UserCreate(BaseModel):
    firebase_uid: str = Field(..., min_length=1)
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    role: UserRole
    school_id: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[UserRole] = None
    school_id: Optional[str] = None
    status: Optional[UserStatus] = None


class UserResponse(BaseModel):
    id: str
    firebase_uid: str
    email: str
    name: str
    role: UserRole
    school_id: Optional[str]
    status: UserStatus
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, user) -> "UserResponse":
        return cls(
            id=user.id,
            firebase_uid=user.firebase_uid,
            email=user.email,
            name=user.name,
            role=user.role,
            school_id=user.school_id,
            status=user.status,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
        )
