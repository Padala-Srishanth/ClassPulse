"""
app.api.v1.monthly_reports — Monthly Reporting & Historical Academic Risk Endpoints
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentUser, get_current_user, require_school_access
from app.core.security import UserRole
from app.schemas.monthly_report import (
    GenerateMonthlyReportRequest,
    MonthlyClassReportResponse,
    MonthlySchoolReportResponse,
    MonthlyStudentReportResponse,
)
from app.services.class_service import ClassService
from app.services.monthly_report_service import MonthlyReportService
from app.services.school_service import SchoolService
from app.services.student_service import StudentService
from app.utils.responses import error_response, success_response

router = APIRouter(tags=["Monthly Reports"])

TEACHER_ROLES = {UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.ADMIN}
ADMIN_ROLES = {UserRole.SCHOOL_ADMIN, UserRole.ADMIN}


def _current_month_str() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m")


# ===========================================================================
# Helper: Check Student Access
# ===========================================================================

def _verify_student_access(student_id: str, current_user: CurrentUser):
    student = StudentService.get_student(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "STUDENT_NOT_FOUND", "message": f"Student '{student_id}' not found."},
        )

    # School isolation
    require_school_access(student.school_id, current_user)

    # If student role, ensure they only access their own record
    if current_user.role == UserRole.STUDENT:
        # Check claims: student_id or user.uid matches student.id
        allowed = (
            getattr(current_user, "student_id", None) == student_id
            or current_user.uid == student_id
            or student_id.startswith("demo-student")  # allow demo student in dev
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Students can only access their own report."},
            )

    return student


# ===========================================================================
# Periods Helper
# ===========================================================================

@router.get("/periods", summary="Get list of available reporting months")
async def list_reporting_periods(
    current_user: CurrentUser = Depends(get_current_user),
):
    # Standard 6-month demo reporting window + current month
    default_periods = ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]
    curr = _current_month_str()
    if curr not in default_periods:
        default_periods.append(curr)
    return success_response(data={"periods": sorted(list(set(default_periods)))})


# ===========================================================================
# Student Monthly Reports
# ===========================================================================

@router.get("/student/{student_id}", summary="Get monthly report for an individual student")
async def get_student_monthly_report(
    student_id: str,
    report_period: str = Query(default=..., description="Report month (YYYY-MM)"),
    current_user: CurrentUser = Depends(get_current_user),
):
    student = _verify_student_access(student_id, current_user)
    report = MonthlyReportService.get_student_report(student.id, report_period, auto_generate=True)
    if not report:
        return error_response(
            code="REPORT_NOT_FOUND",
            message=f"Could not generate report for student {student_id} in {report_period}",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    resp = MonthlyStudentReportResponse.from_model(report)
    return success_response(data=resp.model_dump(mode="json"))


@router.get("/student/{student_id}/history", summary="Get historical monthly reports for a student")
async def get_student_monthly_history(
    student_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    student = _verify_student_access(student_id, current_user)
    reports = MonthlyReportService.list_student_report_history(student.id)
    resp = [MonthlyStudentReportResponse.from_model(r).model_dump(mode="json") for r in reports]
    return success_response(data={"history": resp, "count": len(resp)})


@router.post("/generate/student/{student_id}", summary="Trigger generation of a student monthly report")
async def generate_student_monthly_report(
    student_id: str,
    body: GenerateMonthlyReportRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    student = _verify_student_access(student_id, current_user)
    report = MonthlyReportService.generate_student_report(
        student.id, body.report_period, force=True
    )
    resp = MonthlyStudentReportResponse.from_model(report)
    return success_response(data=resp.model_dump(mode="json"))


# ===========================================================================
# Class Monthly Reports
# ===========================================================================

@router.get("/class/{class_id}", summary="Get aggregated monthly report for a class cohort")
async def get_class_monthly_report(
    class_id: str,
    report_period: str = Query(default=..., description="Report month (YYYY-MM)"),
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.role not in TEACHER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Teachers and school administrators only."},
        )

    class_obj = ClassService.get_class(class_id)
    if not class_obj:
        return error_response(
            code="CLASS_NOT_FOUND",
            message=f"Class '{class_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    require_school_access(class_obj.school_id, current_user)

    report = MonthlyReportService.get_class_report(class_id, report_period, auto_generate=True)
    if not report:
        return error_response(
            code="REPORT_NOT_FOUND",
            message=f"Could not generate class report for {class_id} in {report_period}",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    resp = MonthlyClassReportResponse.from_model(report)
    return success_response(data=resp.model_dump(mode="json"))


@router.post("/generate/class/{class_id}", summary="Trigger generation of a class monthly report")
async def generate_class_monthly_report(
    class_id: str,
    body: GenerateMonthlyReportRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.role not in TEACHER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Teachers and school administrators only."},
        )

    class_obj = ClassService.get_class(class_id)
    if not class_obj:
        return error_response(
            code="CLASS_NOT_FOUND",
            message=f"Class '{class_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    require_school_access(class_obj.school_id, current_user)

    report = MonthlyReportService.generate_class_report(
        class_id, body.report_period, force=True
    )
    resp = MonthlyClassReportResponse.from_model(report)
    return success_response(data=resp.model_dump(mode="json"))


# ===========================================================================
# School Monthly Reports
# ===========================================================================

@router.get("/school/{school_id}", summary="Get school-wide monthly analytics report")
async def get_school_monthly_report(
    school_id: str,
    report_period: str = Query(default=..., description="Report month (YYYY-MM)"),
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "School administrators and principals only."},
        )

    require_school_access(school_id, current_user)

    school = SchoolService.get_school(school_id)
    if not school:
        return error_response(
            code="SCHOOL_NOT_FOUND",
            message=f"School '{school_id}' not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    report = MonthlyReportService.get_school_report(school_id, report_period, auto_generate=True)
    if not report:
        return error_response(
            code="REPORT_NOT_FOUND",
            message=f"Could not generate school report for {school_id} in {report_period}",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    resp = MonthlySchoolReportResponse.from_model(report)
    return success_response(data=resp.model_dump(mode="json"))


@router.post("/generate/school/{school_id}", summary="Trigger generation of a school monthly report")
async def generate_school_monthly_report(
    school_id: str,
    body: GenerateMonthlyReportRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "School administrators and principals only."},
        )

    require_school_access(school_id, current_user)

    report = MonthlyReportService.generate_school_report(
        school_id, body.report_period, force=True
    )
    resp = MonthlySchoolReportResponse.from_model(report)
    return success_response(data=resp.model_dump(mode="json"))
