"""
app.api.v1.students — Student Management Endpoints
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import (
    CurrentUser,
    PaginationParams,
    get_current_user,
    get_pagination,
    require_school_access,
)
from app.schemas.academic import AttendanceResponse, HomeworkResponse, TestScoreResponse
from app.schemas.student import StudentCreate, StudentResponse, StudentUpdate
from app.services.attendance_service import AttendanceService
from app.services.class_service import ClassService
from app.services.homework_service import HomeworkService
from app.services.student_service import StudentService
from app.services.test_score_service import TestScoreService
from app.utils.responses import error_response, success_response

router = APIRouter(tags=["Students"])


@router.post("", summary="Create a new student (ADMIN or SCHOOL_ADMIN)")
async def create_student(
    payload: StudentCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    require_school_access(payload.school_id, current_user)
    if not current_user.is_school_admin:
        return error_response(
            code="AUTH_INSUFFICIENT_ROLE",
            message="Only school administrators can create students.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # Check if student code already exists in school
    existing = StudentService.get_student_by_code(payload.school_id, payload.student_code)
    if existing:
        return error_response(
            code="DUPLICATE_STUDENT_CODE",
            message=f"Student with code '{payload.student_code}' already exists in this school.",
            status_code=status.HTTP_409_CONFLICT,
        )

    student = StudentService.create_student(payload)
    return success_response(
        data=StudentResponse.from_model(student).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/{student_id}", summary="Get student profile")
async def get_student(
    student_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    student = StudentService.get_student(student_id)
    if not student:
        return error_response(
            code="STUDENT_NOT_FOUND",
            message="Student not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    require_school_access(student.school_id, current_user)
    return success_response(data=StudentResponse.from_model(student).model_dump())


@router.patch("/{student_id}", summary="Update student profile (ADMIN or SCHOOL_ADMIN)")
async def update_student(
    student_id: str,
    payload: StudentUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    student = StudentService.get_student(student_id)
    if not student:
        return error_response(
            code="STUDENT_NOT_FOUND",
            message="Student not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    require_school_access(student.school_id, current_user)
    if not current_user.is_school_admin:
        return error_response(
            code="AUTH_INSUFFICIENT_ROLE",
            message="Only school administrators can update students.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    updated = StudentService.update_student(student_id, payload)
    return success_response(data=StudentResponse.from_model(updated).model_dump())


@router.get("/class/{class_id}", summary="List students in a class")
async def list_class_students(
    class_id: str,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: CurrentUser = Depends(get_current_user),
):
    class_obj = ClassService.get_class(class_id)
    if not class_obj:
        return error_response(
            code="CLASS_NOT_FOUND",
            message="Class not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    require_school_access(class_obj.school_id, current_user)
    students = StudentService.list_class_students(class_id, skip=pagination.skip, limit=pagination.limit)
    data = [StudentResponse.from_model(s).model_dump() for s in students]
    return success_response(data=data)


# ---------------------------------------------------------------------------
# Academic Records inspection endpoints for a student
# ---------------------------------------------------------------------------

@router.get("/{student_id}/attendance", summary="Get student attendance records")
async def get_student_attendance(
    student_id: str,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: CurrentUser = Depends(get_current_user),
):
    student = StudentService.get_student(student_id)
    if not student:
        return error_response(code="STUDENT_NOT_FOUND", message="Student not found.", status_code=404)
    require_school_access(student.school_id, current_user)
    records = AttendanceService.list_student_attendance(student_id, skip=pagination.skip, limit=pagination.limit)
    data = [AttendanceResponse.from_model(r).model_dump() for r in records]
    return success_response(data=data)


@router.get("/{student_id}/homework", summary="Get student homework records")
async def get_student_homework(
    student_id: str,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: CurrentUser = Depends(get_current_user),
):
    student = StudentService.get_student(student_id)
    if not student:
        return error_response(code="STUDENT_NOT_FOUND", message="Student not found.", status_code=404)
    require_school_access(student.school_id, current_user)
    records = HomeworkService.list_student_homework(student_id, skip=pagination.skip, limit=pagination.limit)
    data = [HomeworkResponse.from_model(r).model_dump() for r in records]
    return success_response(data=data)


@router.get("/{student_id}/test-scores", summary="Get student test score records")
async def get_student_test_scores(
    student_id: str,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: CurrentUser = Depends(get_current_user),
):
    student = StudentService.get_student(student_id)
    if not student:
        return error_response(code="STUDENT_NOT_FOUND", message="Student not found.", status_code=404)
    require_school_access(student.school_id, current_user)
    records = TestScoreService.list_student_test_scores(student_id, skip=pagination.skip, limit=pagination.limit)
    data = [TestScoreResponse.from_model(r).model_dump() for r in records]
    return success_response(data=data)
