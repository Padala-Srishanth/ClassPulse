"""
app.services.user_service — User Management Service
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from app.core.firebase import get_firestore_client
from app.core.security import UserRole
from app.models.user import User, UserStatus
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    @staticmethod
    def _collection():
        return get_firestore_client().collection("users")

    @classmethod
    def create_user(cls, data: UserCreate) -> User:
        db = cls._collection()
        doc_ref = db.document(data.firebase_uid)
        
        now = datetime.now(tz=timezone.utc)
        user = User(
            id=data.firebase_uid,
            firebase_uid=data.firebase_uid,
            email=str(data.email),
            name=data.name,
            role=data.role,
            school_id=data.school_id,
            status=UserStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        
        doc_ref.set(user.to_firestore())
        return user

    @classmethod
    def get_user(cls, user_id: str) -> Optional[User]:
        doc = cls._collection().document(user_id).get()
        if not doc.exists:
            return None
        return User.from_firestore(doc.id, doc.to_dict())

    @classmethod
    def update_user(cls, user_id: str, data: UserUpdate) -> Optional[User]:
        doc_ref = cls._collection().document(user_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None
        
        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        if not updates:
            return User.from_firestore(doc.id, doc.to_dict())
            
        updates["updated_at"] = datetime.now(tz=timezone.utc)
        if "role" in updates and isinstance(updates["role"], UserRole):
            updates["role"] = updates["role"].value
        if "status" in updates and isinstance(updates["status"], UserStatus):
            updates["status"] = updates["status"].value

        doc_ref.update(updates)
        updated_doc = doc_ref.get()
        return User.from_firestore(updated_doc.id, updated_doc.to_dict())

    @classmethod
    def list_school_users(cls, school_id: str, skip: int = 0, limit: int = 50) -> List[User]:
        query = cls._collection().where("school_id", "==", school_id).offset(skip).limit(limit)
        docs = query.stream()
        return [User.from_firestore(doc.id, doc.to_dict()) for doc in docs]
