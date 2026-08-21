"""
app.schemas.school — School API Request/Response Schemas

Separate from the domain model — these define the API contract.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.school import SchoolStatus


class SchoolCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    code: str = Field(..., min_length=2, max_length=20, pattern=r"^[A-Z0-9\-]+$")
    district: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: str = Field("India", max_length=100)


class SchoolUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    district: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    status: Optional[SchoolStatus] = None


class SchoolResponse(BaseModel):
    id: str
    name: str
    code: str
    district: Optional[str]
    state: Optional[str]
    country: str
    status: SchoolStatus
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, school) -> "SchoolResponse":
        return cls(
            id=school.id,
            name=school.name,
            code=school.code,
            district=school.district,
            state=school.state,
            country=school.country,
            status=school.status,
            created_at=school.created_at.isoformat(),
            updated_at=school.updated_at.isoformat(),
        )
