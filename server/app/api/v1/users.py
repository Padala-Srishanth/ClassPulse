"""
app.api.v1.users — User Profile & Management Endpoints
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import (
    CurrentUser,
    PaginationParams,
    UserRole,
    get_current_user,
    get_pagination,
    require_role,
    require_school_access,
)
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService
from app.utils.responses import error_response, success_response

router = APIRouter(tags=["Users"])


@router.post("", summary="Create application user profile (ADMIN or SCHOOL_ADMIN)")
async def create_user(
    payload: UserCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    if not current_user.is_school_admin:
        return error_response(
            code="AUTH_INSUFFICIENT_ROLE",
            message="Only administrators can create user profiles.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # SCHOOL_ADMIN can only create users in their own school
    if not current_user.is_admin:
        if payload.school_id != current_user.school_id:
            return error_response(
                code="AUTH_SCHOOL_ACCESS_DENIED",
                message="Cannot create user for a different school.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        if payload.role == UserRole.ADMIN:
            return error_response(
                code="AUTH_INSUFFICIENT_ROLE",
                message="School administrators cannot create ADMIN users.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    user = UserService.create_user(payload)
    return success_response(
        data=UserResponse.from_model(user).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/me", summary="Get current logged-in user profile")
async def get_my_profile(
    current_user: CurrentUser = Depends(get_current_user),
):
    user = UserService.get_user(current_user.uid)
    if not user:
        return error_response(
            code="USER_NOT_FOUND",
            message="User profile not found in application database.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return success_response(data=UserResponse.from_model(user).model_dump())


@router.get("/{user_id}", summary="Get user profile by ID (ADMIN or SCHOOL_ADMIN)")
async def get_user(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    user = UserService.get_user(user_id)
    if not user:
        return error_response(
            code="USER_NOT_FOUND",
            message="User not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if user.school_id:
        require_school_access(user.school_id, current_user)
    elif not current_user.is_admin:
        return error_response(
            code="AUTH_INSUFFICIENT_ROLE",
            message="Only platform administrators can access this user.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    return success_response(data=UserResponse.from_model(user).model_dump())


@router.get("/school/{school_id}", summary="List users of a school (ADMIN or SCHOOL_ADMIN)")
async def list_school_users(
    school_id: str,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: CurrentUser = Depends(get_current_user),
):
    require_school_access(school_id, current_user)
    if not current_user.is_school_admin:
        return error_response(
            code="AUTH_INSUFFICIENT_ROLE",
            message="Only school administrators can list school users.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    users = UserService.list_school_users(school_id, skip=pagination.skip, limit=pagination.limit)
    data = [UserResponse.from_model(u).model_dump() for u in users]
    return success_response(data=data)
