"""
app.api.v1.ingestion — CSV Data Ingestion Endpoints
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.api.deps import CurrentUser, get_current_user, require_school_access
from app.services.ingestion_service import IngestionService
from app.utils.responses import success_response

router = APIRouter(tags=["Data Ingestion"])


@router.post("/attendance", summary="Upload attendance CSV")
async def ingest_attendance_csv(
    school_id: str = Form(..., description="Target school ID"),
    file: UploadFile = File(..., description="Attendance CSV file"),
    current_user: CurrentUser = Depends(get_current_user),
):
    require_school_access(school_id, current_user)
    summary = await IngestionService.ingest_attendance(school_id, file)
    return success_response(data=summary.model_dump())


@router.post("/homework", summary="Upload homework CSV")
async def ingest_homework_csv(
    school_id: str = Form(..., description="Target school ID"),
    file: UploadFile = File(..., description="Homework CSV file"),
    current_user: CurrentUser = Depends(get_current_user),
):
    require_school_access(school_id, current_user)
    summary = await IngestionService.ingest_homework(school_id, file)
    return success_response(data=summary.model_dump())


@router.post("/test-scores", summary="Upload test scores CSV")
async def ingest_test_scores_csv(
    school_id: str = Form(..., description="Target school ID"),
    file: UploadFile = File(..., description="Test scores CSV file"),
    current_user: CurrentUser = Depends(get_current_user),
):
    require_school_access(school_id, current_user)
    summary = await IngestionService.ingest_test_scores(school_id, file)
    return success_response(data=summary.model_dump())
