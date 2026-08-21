"""
app.api.v1.risk — AI/ML Early-Warning Risk Detection Endpoints
"""

from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, status

from app.api.deps import (
    CurrentUser,
    PaginationParams,
    get_current_user,
    get_pagination,
    require_school_access,
)
from app.schemas.risk import (
    ClassRiskSummaryResponse,
    RiskAlertResponse,
    StudentRiskAnalysisResponse,
)
from app.services.class_service import ClassService
from app.services.risk_service import RiskService
from app.services.student_service import StudentService
from app.utils.responses import error_response, success_response

router = APIRouter(tags=["Risk Analysis"])


@router.post("/analyze/student/{student_id}", summary="Trigger AI/ML risk analysis for a student")
async def analyze_student(
    student_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    student = StudentService.get_student(student_id)
    if not student:
        return error_response(code="STUDENT_NOT_FOUND", message="Student not found.", status_code=status.HTTP_404_NOT_FOUND)

    require_school_access(student.school_id, current_user)
    result = RiskService.analyze_student_risk(student)
    return success_response(data=result.model_dump())


@router.post("/analyze/class/{class_id}", summary="Trigger AI/ML risk analysis for an entire class")
async def analyze_class(
    class_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    class_obj = ClassService.get_class(class_id)
    if not class_obj:
        return error_response(code="CLASS_NOT_FOUND", message="Class not found.", status_code=status.HTTP_404_NOT_FOUND)

    require_school_access(class_obj.school_id, current_user)
    summary = RiskService.analyze_class_risk(class_id=class_id, school_id=class_obj.school_id)
    return success_response(data=summary.model_dump())


@router.get("/students/{student_id}/latest", summary="Get latest active risk alert for a student")
async def get_latest_student_alert(
    student_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    student = StudentService.get_student(student_id)
    if not student:
        return error_response(code="STUDENT_NOT_FOUND", message="Student not found.", status_code=status.HTTP_404_NOT_FOUND)

    require_school_access(student.school_id, current_user)
    alert = RiskService.get_student_latest_alert(student_id)
    if not alert:
        return error_response(code="ALERT_NOT_FOUND", message="No active risk alert found for student.", status_code=status.HTTP_404_NOT_FOUND)

    return success_response(data=RiskAlertResponse.from_model(alert).model_dump())


@router.get("/students/{student_id}/history", summary="Get historical risk alerts for a student")
async def get_student_risk_history(
    student_id: str,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: CurrentUser = Depends(get_current_user),
):
    student = StudentService.get_student(student_id)
    if not student:
        return error_response(code="STUDENT_NOT_FOUND", message="Student not found.", status_code=status.HTTP_404_NOT_FOUND)

    require_school_access(student.school_id, current_user)
    alerts = RiskService.get_student_alert_history(student_id, skip=pagination.skip, limit=pagination.limit)
    data = [RiskAlertResponse.from_model(a).model_dump() for a in alerts]
    return success_response(data=data)


@router.get("/classes/{class_id}/latest", summary="Get active risk alerts for a class")
async def get_class_active_alerts(
    class_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    class_obj = ClassService.get_class(class_id)
    if not class_obj:
        return error_response(code="CLASS_NOT_FOUND", message="Class not found.", status_code=status.HTTP_404_NOT_FOUND)

    require_school_access(class_obj.school_id, current_user)
    alerts = RiskService.get_class_active_alerts(class_id)
    data = [RiskAlertResponse.from_model(a).model_dump() for a in alerts]
    return success_response(data=data)
