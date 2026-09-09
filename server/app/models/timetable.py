"""
app.models.timetable — Timetable Domain Model

TimetableSlot: One period in a class's weekly schedule.

Collection:
  timetables/{slotId}

Each slot represents one recurring weekly period:
  - A class (class_id) has multiple slots
  - A teacher (teacher_id) has multiple slots across classes
  - day_of_week + period_number + class_id forms a logical unique key
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DayOfWeek(str, Enum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"


# Human-readable day labels for display
DAY_LABELS: dict[str, str] = {
    "MON": "Monday",
    "TUE": "Tuesday",
    "WED": "Wednesday",
    "THU": "Thursday",
    "FRI": "Friday",
    "SAT": "Saturday",
}

# Sort order for days
DAY_ORDER: dict[str, int] = {
    "MON": 0,
    "TUE": 1,
    "WED": 2,
    "THU": 3,
    "FRI": 4,
    "SAT": 5,
}


class TimetableSlot(BaseModel):
    """One period in a class's weekly timetable."""

    id: str                        # Firestore document ID (UUID)
    school_id: str
    class_id: str
    day_of_week: DayOfWeek         # MON, TUE, WED, THU, FRI, SAT
    period_number: int             # 1-based period index within the day
    subject: str
    teacher_id: str                # Firebase UID of the teacher
    teacher_name: str              # Denormalised for display without extra lookup
    start_time: str                # "HH:MM" 24-hour format
    end_time: str                  # "HH:MM" 24-hour format
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @classmethod
    def from_firestore(cls, doc_id: str, data: dict) -> "TimetableSlot":
        data = dict(data)
        data["id"] = doc_id
        for ts_field in ("created_at", "updated_at"):
            if ts_field in data and hasattr(data[ts_field], "timestamp"):
                from datetime import datetime as dt
                data[ts_field] = dt.fromtimestamp(data[ts_field].timestamp(), tz=timezone.utc)
        return cls(**data)

    def to_firestore(self) -> dict:
        d = self.model_dump(exclude={"id"})
        d["day_of_week"] = self.day_of_week.value
        return d
