"""
app.api.v1.timetables — Timetable Management Endpoints

Principal can create/update/delete timetable slots.
Teachers can view class timetables and their own teaching schedule.
Students access their timetable via student_portal.py.

IMPORTANT: Routes with literal path segments (/class/{id}, /my) MUST be
declared before wildcard routes (/{slot_id}) to prevent shadowing.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, get_current_user, require_school_access
from app.core.security import UserRole
from app.schemas.timetable import TimetableSlotCreate, TimetableSlotResponse, TimetableSlotUpdate
from app.services.class_service import ClassService
from app.services.timetable_service import TimetableService
from app.utils.responses import error_response, success_response

router = APIRouter(tags=["Timetables"])


def _require_principal_or_above(user: CurrentUser) -> CurrentUser:
    """Only ADMIN or SCHOOL_ADMIN can manage timetables."""
    if user.role not in {UserRole.ADMIN, UserRole.SCHOOL_ADMIN}:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTH_INSUFFICIENT_ROLE", "message": "Principal access required to manage timetables."},
        )
    return user


def _require_teacher_or_above(user: CurrentUser) -> CurrentUser:
    """TEACHER and above can view timetables."""
    if user.role not in {UserRole.ADMIN, UserRole.SCHOOL_ADMIN, UserRole.TEACHER}:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTH_INSUFFICIENT_ROLE", "message": "Teacher access required."},
        )
    return user


@router.post("", summary="Create a timetable slot (Principal only)")
async def create_timetable_slot(
    payload: TimetableSlotCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_principal_or_above(current_user)
    require_school_access(payload.school_id, current_user)

    cls = ClassService.get_class(payload.class_id)
    if not cls or cls.school_id != payload.school_id:
        return error_response(code="CLASS_NOT_FOUND", message="Class not found.", status_code=404)

    try:
        slot = TimetableService.create_slot(payload)
    except ValueError as e:
        return error_response(code="INVALID_TIME", message=str(e), status_code=422)

    return success_response(
        data=TimetableSlotResponse.from_model(slot).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


# NOTE: /class/{class_id} MUST be declared before /{slot_id}
@router.get("/class/{class_id}", summary="Get timetable for a class")
async def list_class_timetable(
    class_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_teacher_or_above(current_user)
    cls = ClassService.get_class(class_id)
    if not cls:
        return error_response(code="CLASS_NOT_FOUND", message="Class not found.", status_code=404)
    require_school_access(cls.school_id, current_user)

    slots = TimetableService.list_class_slots(class_id)
    return success_response(data=[TimetableSlotResponse.from_model(s).model_dump() for s in slots])


# NOTE: /my MUST be declared before /{slot_id}
@router.get("/my", summary="Get current teacher's own timetable")
async def get_my_timetable(
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_teacher_or_above(current_user)
    slots = TimetableService.list_teacher_slots(current_user.uid)
    return success_response(data=[TimetableSlotResponse.from_model(s).model_dump() for s in slots])


@router.get("/{slot_id}", summary="Get a single timetable slot")
async def get_timetable_slot(
    slot_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_teacher_or_above(current_user)
    slot = TimetableService.get_slot(slot_id)
    if not slot:
        return error_response(code="SLOT_NOT_FOUND", message="Timetable slot not found.", status_code=404)
    require_school_access(slot.school_id, current_user)
    return success_response(data=TimetableSlotResponse.from_model(slot).model_dump())


@router.patch("/{slot_id}", summary="Update a timetable slot (Principal only)")
async def update_timetable_slot(
    slot_id: str,
    payload: TimetableSlotUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_principal_or_above(current_user)
    slot = TimetableService.get_slot(slot_id)
    if not slot:
        return error_response(code="SLOT_NOT_FOUND", message="Timetable slot not found.", status_code=404)
    require_school_access(slot.school_id, current_user)

    try:
        updated = TimetableService.update_slot(slot_id, payload)
    except ValueError as e:
        return error_response(code="INVALID_TIME", message=str(e), status_code=422)

    if not updated:
        return error_response(code="SLOT_NOT_FOUND", message="Timetable slot not found.", status_code=404)
    return success_response(data=TimetableSlotResponse.from_model(updated).model_dump())


@router.delete("/{slot_id}", summary="Delete a timetable slot (Principal only)")
async def delete_timetable_slot(
    slot_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_principal_or_above(current_user)
    slot = TimetableService.get_slot(slot_id)
    if not slot:
        return error_response(code="SLOT_NOT_FOUND", message="Timetable slot not found.", status_code=404)
    require_school_access(slot.school_id, current_user)

    deleted = TimetableService.delete_slot(slot_id)
    if not deleted:
        return error_response(code="SLOT_NOT_FOUND", message="Timetable slot not found.", status_code=404)
    return success_response(data={"deleted": True, "slot_id": slot_id})
