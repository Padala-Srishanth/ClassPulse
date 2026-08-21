"""
app.api.v1.schools — School Management Endpoints
"""

from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import (
    CurrentUser,
    PaginationParams,
    UserRole,
    get_current_user,
    get_pagination,
    require_role,
    require_school_access,
)
from app.schemas.school import SchoolCreate, SchoolResponse, SchoolUpdate
from app.services.school_service import SchoolService
from app.utils.responses import error_response, success_response

router = APIRouter(tags=["Schools"])


@router.post("", summary="Create a new school (ADMIN only)")
async def create_school(
    payload: SchoolCreate,
    user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
):
    school = SchoolService.create_school(payload)
    return success_response(
        data=SchoolResponse.from_model(school).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("", summary="List all schools (ADMIN only)")
async def list_schools(
    pagination: PaginationParams = Depends(get_pagination),
    user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
):
    schools = SchoolService.list_schools(skip=pagination.skip, limit=pagination.limit)
    data = [SchoolResponse.from_model(s).model_dump() for s in schools]
    return success_response(data=data)


@router.get("/{school_id}", summary="Get school details")
async def get_school(
    school_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    require_school_access(school_id, user)
    school = SchoolService.get_school(school_id)
    if not school:
        return error_response(
            code="SCHOOL_NOT_FOUND",
            message="School not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return success_response(data=SchoolResponse.from_model(school).model_dump())


@router.patch("/{school_id}", summary="Update school details (ADMIN or SCHOOL_ADMIN)")
async def update_school(
    school_id: str,
    payload: SchoolUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    require_school_access(school_id, user)
    if not user.is_school_admin:
        return error_response(
            code="AUTH_INSUFFICIENT_ROLE",
            message="Only school administrators can update school details.",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    school = SchoolService.update_school(school_id, payload)
    if not school:
        return error_response(
            code="SCHOOL_NOT_FOUND",
            message="School not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return success_response(data=SchoolResponse.from_model(school).model_dump())
