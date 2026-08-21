"""
app.schemas.ingestion — CSV Ingestion Schemas
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class RowError(BaseModel):
    row_number: int
    error: str


class ImportSummary(BaseModel):
    batch_id: str
    total_rows: int
    successful_rows: int
    failed_rows: int
    duplicate_rows: int
    errors: List[RowError] = []
