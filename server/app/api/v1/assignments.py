"""
app.api.v1.assignments — Assignment & Classwork Endpoints
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentUser, get_current_user
from app.models.user import UserRole
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
    SchoolAssignmentStatsResponse,
    SubmissionGradeUpdate,
    SubmissionResponse,
)
from app.utils.responses import error_response, success_response
from app.services.assignment_service import AssignmentService
from app.services.class_service import ClassService

router = APIRouter(tags=["assignments"])


def _require_staff(current_user: CurrentUser):
    if current_user.role not in (UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTH_FORBIDDEN", "message": "Only teachers and administrators can manage assignments."},
        )


def _require_principal_or_above(current_user: CurrentUser):
    if current_user.role not in (UserRole.SCHOOL_ADMIN, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTH_FORBIDDEN", "message": "Only school administrators can access this endpoint."},
        )


@router.post("", summary="Create a new assignment")
async def create_assignment(
    body: AssignmentCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_staff(current_user)

    # Verify class exists and belongs to user's school
    cls_obj = ClassService.get_class(body.class_id)
    if not cls_obj:
        raise HTTPException(status_code=404, detail={"code": "CLASS_NOT_FOUND", "message": "Class not found."})
    if cls_obj.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail={"code": "AUTH_SCHOOL_ACCESS_DENIED", "message": "Access denied."})

    teacher_id = current_user.uid
    from app.services.user_service import UserService
    user_doc = UserService.get_user(current_user.uid)
    teacher_name = user_doc.name if user_doc and user_doc.name else (current_user.email or "Teacher")

    assignment = AssignmentService.create_assignment(
        school_id=current_user.school_id,
        class_id=body.class_id,
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        title=body.title,
        subject=body.subject,
        due_date=body.due_date,
        due_time=body.due_time or "23:59",
        max_marks=body.max_marks,
        description=body.description or "",
        attachments=body.attachments or [],
    )

    tot, sub_cnt, grd_cnt, late_cnt = AssignmentService.get_assignment_metrics(assignment.id, assignment.class_id)
    resp = AssignmentResponse.from_model(assignment, tot, sub_cnt, grd_cnt, late_cnt)
    return success_response(data=resp.model_dump(mode="json"), status_code=201)


@router.get("/stats/overview", summary="Principal school-wide assignment statistics")
async def get_assignment_stats(
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_principal_or_above(current_user)
    stats = AssignmentService.get_school_assignment_stats(current_user.school_id)
    return success_response(data=stats)


@router.get("", summary="List assignments")
async def list_assignments(
    class_id: Optional[str] = Query(None, description="Filter by class ID"),
    teacher_id: Optional[str] = Query(None, description="Filter by teacher ID"),
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_staff(current_user)

    if class_id:
        cls_obj = ClassService.get_class(class_id)
        if not cls_obj:
            raise HTTPException(status_code=404, detail={"code": "CLASS_NOT_FOUND", "message": "Class not found."})
        if cls_obj.school_id != current_user.school_id:
            raise HTTPException(status_code=403, detail={"code": "AUTH_SCHOOL_ACCESS_DENIED", "message": "Access denied."})
        assignments = AssignmentService.list_class_assignments(class_id)
    elif teacher_id:
        assignments = AssignmentService.list_teacher_assignments(teacher_id, current_user.school_id)
    else:
        if current_user.role == UserRole.TEACHER:
            assignments = AssignmentService.list_teacher_assignments(current_user.uid, current_user.school_id)
        else:
            assignments = AssignmentService.list_school_assignments(current_user.school_id)

    result = []
    for a in assignments:
        tot, sub_cnt, grd_cnt, late_cnt = AssignmentService.get_assignment_metrics(a.id, a.class_id)
        result.append(AssignmentResponse.from_model(a, tot, sub_cnt, grd_cnt, late_cnt).model_dump(mode="json"))

    return success_response(data=result)


@router.get("/{assignment_id}", summary="Get assignment details")
async def get_assignment(
    assignment_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_staff(current_user)
    assignment = AssignmentService.get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail={"code": "ASSIGNMENT_NOT_FOUND", "message": "Assignment not found."})
    if assignment.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail={"code": "AUTH_SCHOOL_ACCESS_DENIED", "message": "Access denied."})

    tot, sub_cnt, grd_cnt, late_cnt = AssignmentService.get_assignment_metrics(assignment.id, assignment.class_id)
    resp = AssignmentResponse.from_model(assignment, tot, sub_cnt, grd_cnt, late_cnt)
    return success_response(data=resp.model_dump(mode="json"))


@router.put("/{assignment_id}", summary="Update assignment details")
async def update_assignment(
    assignment_id: str,
    body: AssignmentUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_staff(current_user)
    assignment = AssignmentService.get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail={"code": "ASSIGNMENT_NOT_FOUND", "message": "Assignment not found."})
    if assignment.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail={"code": "AUTH_SCHOOL_ACCESS_DENIED", "message": "Access denied."})

    # Only creator teacher or school admin can modify
    if current_user.role == UserRole.TEACHER and assignment.teacher_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail={"code": "AUTH_FORBIDDEN", "message": "Teachers can only modify their own assignments."},
        )

    updated = AssignmentService.update_assignment(assignment_id, body.model_dump(exclude_unset=True))
    tot, sub_cnt, grd_cnt, late_cnt = AssignmentService.get_assignment_metrics(updated.id, updated.class_id)
    resp = AssignmentResponse.from_model(updated, tot, sub_cnt, grd_cnt, late_cnt)
    return success_response(data=resp.model_dump(mode="json"))


@router.delete("/{assignment_id}", summary="Delete an assignment")
async def delete_assignment(
    assignment_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_staff(current_user)
    assignment = AssignmentService.get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail={"code": "ASSIGNMENT_NOT_FOUND", "message": "Assignment not found."})
    if assignment.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail={"code": "AUTH_SCHOOL_ACCESS_DENIED", "message": "Access denied."})

    if current_user.role == UserRole.TEACHER and assignment.teacher_id != current_user.uid:
        raise HTTPException(
            status_code=403,
            detail={"code": "AUTH_FORBIDDEN", "message": "Teachers can only delete their own assignments."},
        )

    AssignmentService.delete_assignment(assignment_id)
    return success_response(data={"message": "Assignment deleted successfully."})


@router.get("/{assignment_id}/submissions", summary="List class roster submissions for assignment")
async def list_submissions(
    assignment_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_staff(current_user)
    assignment = AssignmentService.get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail={"code": "ASSIGNMENT_NOT_FOUND", "message": "Assignment not found."})
    if assignment.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail={"code": "AUTH_SCHOOL_ACCESS_DENIED", "message": "Access denied."})

    roster = AssignmentService.list_assignment_submissions(assignment_id, assignment.class_id)
    return success_response(data=roster)


@router.put("/{assignment_id}/submissions/{student_id}/grade", summary="Grade a student submission")
async def grade_submission(
    assignment_id: str,
    student_id: str,
    body: SubmissionGradeUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_staff(current_user)
    assignment = AssignmentService.get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail={"code": "ASSIGNMENT_NOT_FOUND", "message": "Assignment not found."})
    if assignment.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail={"code": "AUTH_SCHOOL_ACCESS_DENIED", "message": "Access denied."})

    try:
        sub = AssignmentService.grade_submission(
            assignment_id=assignment_id,
            student_id=student_id,
            obtained_marks=body.obtained_marks,
            feedback=body.feedback,
            teacher_id=current_user.uid,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"code": "INVALID_GRADE", "message": str(e)})

    return success_response(data=SubmissionResponse.from_model(sub).model_dump(mode="json"))
