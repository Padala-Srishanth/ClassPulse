"""
app.models.school — School Domain Model

Internal representation of a ClassPulse school (tenant).
This is separate from the API schema — internal code uses this model.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SchoolStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class School(BaseModel):
    """Internal domain model for a school."""

    id: str
    name: str
    code: str                        # Short unique identifier (e.g. "DPS-DEL")
    district: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    status: SchoolStatus = SchoolStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "School":
        """Build a School from a Firestore document."""
        data = dict(data)
        data["id"] = doc_id
        # Firestore timestamps → datetime
        for ts_field in ("created_at", "updated_at"):
            if ts_field in data and hasattr(data[ts_field], "timestamp"):
                import datetime as dt
                data[ts_field] = datetime.fromtimestamp(
                    data[ts_field].timestamp(), tz=timezone.utc
                )
        return cls(**data)

    def to_firestore(self) -> dict:
        """Serialize to Firestore document (exclude id — it's the doc key)."""
        d = self.model_dump(exclude={"id"})
        d["status"] = self.status.value
        return d
