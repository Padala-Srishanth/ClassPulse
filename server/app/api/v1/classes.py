"""
app.api.v1.classes — Class Management Endpoints
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
from app.schemas.academic import BulkClassAttendanceCreate
from app.schemas.class_ import ClassCreate, ClassResponse, ClassUpdate
from app.services.class_service import ClassService
from app.utils.responses import error_response, success_response


router = APIRouter(tags=["Classes"])


@router.post("", summary="Create a new class (ADMIN or SCHOOL_ADMIN)")
async def create_class(
    payload: ClassCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    require_school_access(payload.school_id, current_user)
    if not current_user.is_school_admin:
        return error_response(
            code="AUTH_INSUFFICIENT_ROLE",
            message="Only school administrators can create classes.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    class_obj = ClassService.create_class(payload)
    return success_response(
        data=ClassResponse.from_model(class_obj).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/{class_id}", summary="Get class details")
async def get_class(
    class_id: str,
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
    return success_response(data=ClassResponse.from_model(class_obj).model_dump())


@router.patch("/{class_id}", summary="Update class details (ADMIN or SCHOOL_ADMIN)")
async def update_class(
    class_id: str,
    payload: ClassUpdate,
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
    if not current_user.is_school_admin:
        return error_response(
            code="AUTH_INSUFFICIENT_ROLE",
            message="Only school administrators can update classes.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    updated = ClassService.update_class(class_id, payload)
    return success_response(data=ClassResponse.from_model(updated).model_dump())


@router.get("/school/{school_id}", summary="List classes in a school")
async def list_school_classes(
    school_id: str,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: CurrentUser = Depends(get_current_user),
):
    require_school_access(school_id, current_user)
    classes = ClassService.list_school_classes(school_id, skip=pagination.skip, limit=pagination.limit)
    data = [ClassResponse.from_model(c).model_dump() for c in classes]
    return success_response(data=data)


@router.post("/{class_id}/attendance", summary="Record class-wide attendance for a date")
async def record_class_attendance(
    class_id: str,
    payload: BulkClassAttendanceCreate,
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

    from app.services.attendance_service import AttendanceService
    count = AttendanceService.record_bulk_class_attendance(
        school_id=class_obj.school_id,
        class_id=class_id,
        date=payload.date,
        entries=payload.records,
    )
    return success_response(
        data={"recorded_count": count, "date": payload.date, "class_id": class_id},
        status_code=status.HTTP_200_OK,
    )

