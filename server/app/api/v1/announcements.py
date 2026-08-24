"""
app.api.v1.announcements — Announcement Endpoints

Principal can create school-wide / teacher / student announcements.
Teachers can create class announcements.
All authenticated users can read their relevant announcements.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, get_current_user
from app.core.security import UserRole
from app.models.announcement import AnnouncementTarget
from app.schemas.announcement import AnnouncementCreate, AnnouncementResponse
from app.services.announcement_service import AnnouncementService
from app.utils.responses import error_response, success_response

router = APIRouter(tags=["Announcements"])


@router.post("", summary="Create an announcement")
async def create_announcement(
    payload: AnnouncementCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    school_id = current_user.school_id or "school-001"

    # Only principal can send school-wide or teacher announcements
    if payload.target in (AnnouncementTarget.ALL_SCHOOL, AnnouncementTarget.TEACHERS):
        if current_user.role not in {UserRole.ADMIN, UserRole.SCHOOL_ADMIN}:
            return error_response(
                code="AUTH_INSUFFICIENT_ROLE",
                message="Only school admin can send school-wide or teacher announcements.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    ann = AnnouncementService.create_announcement(
        school_id=school_id,
        created_by=current_user.uid,
        created_by_name=current_user.email or "Unknown",
        title=payload.title,
        message=payload.message,
        target=payload.target,
        target_class_id=payload.target_class_id,
        expires_at=payload.expires_at,
    )
    return success_response(
        data=AnnouncementResponse.from_model(ann).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("", summary="Get announcements for current user")
async def list_announcements(
    class_id: Optional[str] = Query(None, description="Filter by class"),
    current_user: CurrentUser = Depends(get_current_user),
):
    school_id = current_user.school_id or "school-001"

    if current_user.role in {UserRole.ADMIN, UserRole.SCHOOL_ADMIN}:
        announcements = AnnouncementService.list_school_announcements(school_id)
    elif current_user.role == UserRole.TEACHER:
        announcements = AnnouncementService.list_for_teachers(school_id)
    elif current_user.role == UserRole.STUDENT:
        announcements = AnnouncementService.list_for_students(school_id, class_id)
    else:
        announcements = []

    data = [AnnouncementResponse.from_model(a).model_dump() for a in announcements]
    return success_response(data=data)
