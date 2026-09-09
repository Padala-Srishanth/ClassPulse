"""
app.api.v1.doubts - Doubt Discussion API Endpoints

RBAC:
  POST   /doubts                     - Student: post a doubt
  GET    /doubts                     - Teacher/Admin: list class doubts
  GET    /doubts/{id}                - Teacher/Admin/Student (own class)
  PUT    /doubts/{id}                - Teacher/Admin: update status
  DELETE /doubts/{id}                - Teacher/Admin: delete
  POST   /doubts/{id}/replies        - Teacher/Student: post a reply
  GET    /doubts/{id}/replies        - Teacher/Student: list replies
  DELETE /doubts/{id}/replies/{rid}  - Author or Teacher: delete reply
  POST   /doubts/{id}/mark-answered  - Teacher: mark a reply as verified answer
  POST   /doubts/{id}/close          - Teacher/Admin: close doubt
  GET    /doubts/stats/school        - Principal: school-wide analytics
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from fastapi import HTTPException

from app.api.deps import CurrentUser, get_current_user
from app.core.security import UserRole
from app.schemas.doubt import (
    DoubtCreate,
    DoubtUpdate,
    DoubtReplyCreate,
    DoubtResponse,
    DoubtReplyResponse,
)
from app.services.doubt_service import DoubtService
from app.services.student_service import StudentService
from app.utils.responses import error_response, success_response

router = APIRouter(tags=["Doubts"])

TEACHER_ROLES = {UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.ADMIN}
ADMIN_ROLES = {UserRole.SCHOOL_ADMIN, UserRole.ADMIN}


def _require_teacher_or_above(user: CurrentUser):
    if user.role not in TEACHER_ROLES:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Teachers and above only."})


def _require_student(user: CurrentUser):
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Students only."})


# ---------------------------------------------------------------------------
# GET /stats/school ? must come BEFORE /{doubt_id} to avoid path conflict
# ---------------------------------------------------------------------------

@router.get("/stats/school", summary="School-wide doubt analytics (Principal)")
async def school_doubt_stats(
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_teacher_or_above(current_user)
    school_id = current_user.school_id or "school-001"
    stats = DoubtService.get_school_doubt_stats(school_id)
    return success_response(data=stats)


# ---------------------------------------------------------------------------
# POST /doubts ? student posts a doubt
# ---------------------------------------------------------------------------

@router.post("", summary="Post a new doubt (Student)", status_code=status.HTTP_201_CREATED)
async def create_doubt(
    body: DoubtCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_student(current_user)
    school_id = current_user.school_id or "school-001"
    student_id = getattr(current_user, "student_id", None) or current_user.uid

    # Derive student name from student profile
    student_name = "Student"
    if student_id:
        stu = StudentService.get_student(student_id)
        if stu:
            student_name = stu.name

    from app.models.doubt import DoubtVisibility
    vis = DoubtVisibility(body.visibility) if body.visibility else DoubtVisibility.CLASS

    doubt = DoubtService.create_doubt(
        school_id=school_id,
        class_id=body.class_id,
        student_id=student_id,
        student_name=student_name,
        title=body.title,
        body=body.body,
        subject=body.subject,
        attachment_name=body.attachment_name,
        attachment_url=body.attachment_url,
        visibility=vis,
    )
    return success_response(data=DoubtResponse.from_model(doubt).model_dump(mode="json"), status_code=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# GET /doubts?class_id=...&subject=...&status=...
# ---------------------------------------------------------------------------

@router.get("", summary="List doubts for a class")
async def list_doubts(
    class_id: str = Query(..., description="Class ID to filter by"),
    subject: str = Query(None),
    status_filter: str = Query(None, alias="status"),
    current_user: CurrentUser = Depends(get_current_user),
):
    school_id = current_user.school_id or "school-001"

    doubts = DoubtService.list_class_doubts(class_id, subject=subject, status=status_filter)
    # Students see CLASS-visibility doubts from their own class only (non-private)
    if current_user.role == UserRole.STUDENT:
        student_id = getattr(current_user, "student_id", None) or current_user.uid
        doubts = [
            d for d in doubts
            if d.school_id == school_id and (
                d.visibility.value == "CLASS" or d.student_id == student_id
            )
        ]
    else:
        doubts = [d for d in doubts if d.school_id == school_id]

    return success_response(data=[DoubtResponse.from_model(d).model_dump(mode="json") for d in doubts])


# ---------------------------------------------------------------------------
# GET /doubts/{doubt_id}
# ---------------------------------------------------------------------------

@router.get("/{doubt_id}", summary="Get a single doubt with replies")
async def get_doubt(
    doubt_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    doubt = DoubtService.get_doubt(doubt_id)
    if not doubt:
        raise HTTPException(status_code=404, detail={"code": "DOUBT_NOT_FOUND", "message": "Doubt not found."})

    school_id = current_user.school_id or "school-001"
    if doubt.school_id != school_id:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Access denied."})

    # Students can only see CLASS doubts or their own PRIVATE doubts
    if current_user.role == UserRole.STUDENT:
        student_id = getattr(current_user, "student_id", None) or current_user.uid
        if doubt.visibility.value == "PRIVATE" and doubt.student_id != student_id:
            raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Private doubt."})

    replies = DoubtService.list_replies(doubt_id)
    return success_response(data={
        "doubt": DoubtResponse.from_model(doubt).model_dump(mode="json"),
        "replies": [DoubtReplyResponse.from_model(r).model_dump(mode="json") for r in replies],
    })


# ---------------------------------------------------------------------------
# PUT /doubts/{doubt_id} ? teacher/admin update
# ---------------------------------------------------------------------------

@router.put("/{doubt_id}", summary="Update doubt (Teacher/Admin)")
async def update_doubt(
    doubt_id: str,
    body: DoubtUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_teacher_or_above(current_user)
    doubt = DoubtService.get_doubt(doubt_id)
    if not doubt:
        raise HTTPException(status_code=404, detail={"code": "DOUBT_NOT_FOUND", "message": "Doubt not found."})

    school_id = current_user.school_id or "school-001"
    if doubt.school_id != school_id:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Access denied."})

    updates = body.model_dump(exclude_none=True)
    updated = DoubtService.update_doubt(doubt_id, updates)
    return success_response(data=DoubtResponse.from_model(updated).model_dump(mode="json"))


# ---------------------------------------------------------------------------
# DELETE /doubts/{doubt_id}
# ---------------------------------------------------------------------------

@router.delete("/{doubt_id}", summary="Delete doubt (Teacher/Admin)")
async def delete_doubt(
    doubt_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_teacher_or_above(current_user)
    doubt = DoubtService.get_doubt(doubt_id)
    if not doubt:
        raise HTTPException(status_code=404, detail={"code": "DOUBT_NOT_FOUND", "message": "Doubt not found."})

    school_id = current_user.school_id or "school-001"
    if doubt.school_id != school_id:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Access denied."})

    DoubtService.delete_doubt(doubt_id)
    return success_response(data={"deleted": True})


# ---------------------------------------------------------------------------
# POST /doubts/{doubt_id}/replies
# ---------------------------------------------------------------------------

@router.post("/{doubt_id}/replies", summary="Post a reply to a doubt", status_code=status.HTTP_201_CREATED)
async def add_reply(
    doubt_id: str,
    body: DoubtReplyCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    doubt = DoubtService.get_doubt(doubt_id)
    if not doubt:
        raise HTTPException(status_code=404, detail={"code": "DOUBT_NOT_FOUND", "message": "Doubt not found."})

    school_id = current_user.school_id or "school-001"
    if doubt.school_id != school_id:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Access denied."})

    # Determine author details
    author_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    author_name = current_user.email or "User"

    # For teachers, use their name from profile if possible
    if current_user.role in TEACHER_ROLES:
        from app.services.user_service import UserService
        try:
            user = UserService.get_user(current_user.uid)
            if user:
                author_name = user.name or author_name
        except Exception:
            pass
    else:
        # Student ? get name from student profile
        student_id = getattr(current_user, "student_id", None) or current_user.uid
        stu = StudentService.get_student(student_id)
        if stu:
            author_name = stu.name

    reply = DoubtService.add_reply(
        doubt_id=doubt_id,
        school_id=school_id,
        class_id=doubt.class_id,
        author_id=current_user.uid,
        author_name=author_name,
        author_role=author_role,
        body=body.body,
        attachment_name=body.attachment_name,
        attachment_url=body.attachment_url,
    )
    return success_response(data=DoubtReplyResponse.from_model(reply).model_dump(mode="json"), status_code=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# GET /doubts/{doubt_id}/replies
# ---------------------------------------------------------------------------

@router.get("/{doubt_id}/replies", summary="List replies for a doubt")
async def list_replies(
    doubt_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    doubt = DoubtService.get_doubt(doubt_id)
    if not doubt:
        raise HTTPException(status_code=404, detail={"code": "DOUBT_NOT_FOUND", "message": "Doubt not found."})

    school_id = current_user.school_id or "school-001"
    if doubt.school_id != school_id:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Access denied."})

    replies = DoubtService.list_replies(doubt_id)
    return success_response(data=[DoubtReplyResponse.from_model(r).model_dump(mode="json") for r in replies])


# ---------------------------------------------------------------------------
# DELETE /doubts/{doubt_id}/replies/{reply_id}
# ---------------------------------------------------------------------------

@router.delete("/{doubt_id}/replies/{reply_id}", summary="Delete a reply")
async def delete_reply(
    doubt_id: str,
    reply_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    doubt = DoubtService.get_doubt(doubt_id)
    if not doubt:
        raise HTTPException(status_code=404, detail={"code": "DOUBT_NOT_FOUND", "message": "Doubt not found."})

    school_id = current_user.school_id or "school-001"
    if doubt.school_id != school_id:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Access denied."})

    # Only teacher/admin can delete any reply; students can only delete their own
    if current_user.role == UserRole.STUDENT:
        replies = DoubtService.list_replies(doubt_id)
        target = next((r for r in replies if r.id == reply_id), None)
        if not target:
            raise HTTPException(status_code=404, detail={"code": "REPLY_NOT_FOUND", "message": "Reply not found."})
        if target.author_id != current_user.uid:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Cannot delete another user reply."})

    deleted = DoubtService.delete_reply(doubt_id, reply_id)
    if not deleted:
        raise HTTPException(status_code=404, detail={"code": "REPLY_NOT_FOUND", "message": "Reply not found."})
    return success_response(data={"deleted": True})


# ---------------------------------------------------------------------------
# POST /doubts/{doubt_id}/mark-answered
# ---------------------------------------------------------------------------

@router.post("/{doubt_id}/mark-answered", summary="Mark a reply as verified answer (Teacher)")
async def mark_answered(
    doubt_id: str,
    reply_id: str = Query(..., description="The reply ID to mark as verified answer"),
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_teacher_or_above(current_user)
    doubt = DoubtService.get_doubt(doubt_id)
    if not doubt:
        raise HTTPException(status_code=404, detail={"code": "DOUBT_NOT_FOUND", "message": "Doubt not found."})

    school_id = current_user.school_id or "school-001"
    if doubt.school_id != school_id:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Access denied."})

    teacher_name = current_user.email or "Teacher"
    from app.services.user_service import UserService
    try:
        user = UserService.get_user(current_user.uid)
        if user:
            teacher_name = user.name or teacher_name
    except Exception:
        pass

    updated = DoubtService.mark_as_answered(doubt_id, reply_id, current_user.uid, teacher_name)
    if not updated:
        raise HTTPException(status_code=404, detail={"code": "REPLY_NOT_FOUND", "message": "Reply not found."})
    return success_response(data=DoubtResponse.from_model(updated).model_dump(mode="json"))


# ---------------------------------------------------------------------------
# POST /doubts/{doubt_id}/close
# ---------------------------------------------------------------------------

@router.post("/{doubt_id}/close", summary="Close a doubt (Teacher/Admin)")
async def close_doubt(
    doubt_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_teacher_or_above(current_user)
    doubt = DoubtService.get_doubt(doubt_id)
    if not doubt:
        raise HTTPException(status_code=404, detail={"code": "DOUBT_NOT_FOUND", "message": "Doubt not found."})

    school_id = current_user.school_id or "school-001"
    if doubt.school_id != school_id:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Access denied."})

    updated = DoubtService.close_doubt(doubt_id)
    return success_response(data=DoubtResponse.from_model(updated).model_dump(mode="json"))
