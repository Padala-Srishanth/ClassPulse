"""
app.schemas.timetable — Timetable API Request/Response Schemas
"""

from __future__ import annotations

import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.timetable import DayOfWeek


def _validate_time(v: str) -> str:
    """Validate HH:MM 24-hour time format."""
    if not re.match(r"^\d{2}:\d{2}$", v):
        raise ValueError("Time must be in HH:MM format (e.g. '09:00')")
    h, m = int(v[:2]), int(v[3:])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError("Invalid time value")
    return v


class TimetableSlotCreate(BaseModel):
    school_id: str = Field(..., min_length=1)
    class_id: str = Field(..., min_length=1)
    day_of_week: DayOfWeek
    period_number: int = Field(..., ge=1, le=12)
    subject: str = Field(..., min_length=1, max_length=100)
    teacher_id: str = Field(..., min_length=1)
    teacher_name: str = Field(..., min_length=1, max_length=200)
    start_time: str = Field(..., description="HH:MM 24-hour format")
    end_time: str = Field(..., description="HH:MM 24-hour format")

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        return _validate_time(v)

    def validate_time_order(self) -> None:
        """Call after construction to verify start < end."""
        if self.start_time >= self.end_time:
            raise ValueError(f"start_time ({self.start_time}) must be before end_time ({self.end_time})")


class TimetableSlotUpdate(BaseModel):
    day_of_week: Optional[DayOfWeek] = None
    period_number: Optional[int] = Field(None, ge=1, le=12)
    subject: Optional[str] = Field(None, min_length=1, max_length=100)
    teacher_id: Optional[str] = None
    teacher_name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return _validate_time(v)
        return v


class TimetableSlotResponse(BaseModel):
    id: str
    school_id: str
    class_id: str
    day_of_week: str
    period_number: int
    subject: str
    teacher_id: str
    teacher_name: str
    start_time: str
    end_time: str
    created_at: str

    @classmethod
    def from_model(cls, slot) -> "TimetableSlotResponse":
        return cls(
            id=slot.id,
            school_id=slot.school_id,
            class_id=slot.class_id,
            day_of_week=slot.day_of_week.value,
            period_number=slot.period_number,
            subject=slot.subject,
            teacher_id=slot.teacher_id,
            teacher_name=slot.teacher_name,
            start_time=slot.start_time,
            end_time=slot.end_time,
            created_at=slot.created_at.isoformat(),
        )
