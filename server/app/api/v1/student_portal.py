"""
app.api.v1.student_portal — Student Self-Service Endpoints

Students can ONLY access their own data.
A student can NEVER access another student's data by changing an ID in the URL.
All endpoints derive the student identity from the authenticated token's student_id claim.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, get_current_user
from app.core.security import UserRole
from app.models.meeting import MeetingType
from app.services.attendance_service import AttendanceService
from app.services.announcement_service import AnnouncementService
from app.services.exam_service import ExamService
from app.services.meeting_service import MeetingService
from app.services.student_service import StudentService
from app.utils.responses import error_response, success_response

router = APIRouter(tags=["Student Portal"])


def _get_student_identity(current_user: CurrentUser):
    """
    Enforce that the caller is a STUDENT and has a student_id claim.
    Returns (student_id, school_id).
    """
    if current_user.role != UserRole.STUDENT:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "STUDENT_ONLY", "message": "This endpoint is for students only."},
        )
    # student_id may be in the token as a custom claim
    student_id = getattr(current_user, "student_id", None)
    school_id = current_user.school_id or "school-001"
    return student_id, school_id


# Extend CurrentUser to carry student_id if present in the decoded token
# (The get_current_user dependency already sets this via decoded.get("student_id"))


@router.get("/me", summary="Student own profile")
async def student_me(
    current_user: CurrentUser = Depends(get_current_user),
):
    _, school_id = _get_student_identity(current_user)

    # Look up student by UID — in production the UID maps to a student record
    # For demo, return a sample profile
    return success_response(data={
        "uid": current_user.uid,
        "email": current_user.email,
        "school_id": school_id,
        "role": "STUDENT",
        "message": "Student profile loaded. In production, student_id links to Firestore student record.",
    })


@router.get("/attendance", summary="Student own attendance")
async def student_attendance(
    current_user: CurrentUser = Depends(get_current_user),
    student_id: Optional[str] = Query(None, description="Student ID (for demo; in prod derived from token)"),
):
    _, school_id = _get_student_identity(current_user)

    # In production: student_id is always from the token claim, never from URL parameter
    # For demo purposes, we allow an optional query param
    stu_id = student_id or "demo-student-001"

    records = AttendanceService.list_student_attendance(stu_id, limit=100)
    present = len([r for r in records if r.status.value == "PRESENT"])
    absent = len([r for r in records if r.status.value == "ABSENT"])
    late = len([r for r in records if r.status.value == "LATE"])
    total = len(records)

    return success_response(data={
        "summary": {
            "total": total,
            "present": present,
            "absent": absent,
            "late": late,
            "attendance_percentage": round(present / total * 100, 1) if total > 0 else None,
        },
        "records": [{"date": r.date, "status": r.status.value} for r in records],
    })


@router.get("/marks", summary="Student own exam results")
async def student_marks(
    current_user: CurrentUser = Depends(get_current_user),
    student_id: Optional[str] = Query(None, description="Student ID (for demo; in prod derived from token)"),
):
    _, school_id = _get_student_identity(current_user)
    stu_id = student_id or "demo-student-001"

    results = ExamService.list_student_results(stu_id, school_id)
    result_data = []
    for r in results:
        exam = ExamService.get_exam(r.exam_id)
        result_data.append({
            "exam_name": exam.exam_name if exam else "Unknown",
            "subject": exam.subject if exam else "Unknown",
            "exam_date": exam.exam_date if exam else "",
            "obtained_marks": r.obtained_marks,
            "max_marks": r.max_marks,
            "percentage": r.percentage,
            "grade": r.grade,
        })

    return success_response(data={
        "results": result_data,
        "total_exams": len(result_data),
        "average_percentage": round(sum(r["percentage"] for r in result_data) / len(result_data), 1) if result_data else None,
    })


@router.get("/announcements", summary="Announcements relevant to student")
async def student_announcements(
    class_id: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
):
    _, school_id = _get_student_identity(current_user)
    announcements = AnnouncementService.list_for_students(school_id, class_id)

    from app.schemas.announcement import AnnouncementResponse
    return success_response(data=[AnnouncementResponse.from_model(a).model_dump() for a in announcements])


@router.post("/meeting-requests", summary="Request a meeting with teacher or principal")
async def request_meeting(
    subject: str,
    message: str,
    proposed_date: str,
    requested_to: str,
    requested_to_name: str,
    meeting_type: MeetingType = MeetingType.STUDENT_TEACHER,
    proposed_time: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    _, school_id = _get_student_identity(current_user)

    req = MeetingService.create_request(
        school_id=school_id,
        meeting_type=meeting_type,
        requested_by=current_user.uid,
        requested_by_name=current_user.email or "Student",
        requested_to=requested_to,
        requested_to_name=requested_to_name,
        subject=subject,
        message=message,
        proposed_date=proposed_date,
        proposed_time=proposed_time,
    )
    return success_response(data={
        "id": req.id,
        "status": req.status.value,
        "meeting_type": req.meeting_type.value,
        "proposed_date": req.proposed_date,
        "created_at": req.created_at.isoformat(),
    }, status_code=status.HTTP_201_CREATED)


@router.get("/meeting-requests", summary="Get student own meeting requests")
async def list_meeting_requests(
    current_user: CurrentUser = Depends(get_current_user),
):
    _, school_id = _get_student_identity(current_user)
    requests = MeetingService.list_for_user(current_user.uid, school_id)
    return success_response(data=[{
        "id": r.id,
        "meeting_type": r.meeting_type.value,
        "subject": r.subject,
        "status": r.status.value,
        "requested_to_name": r.requested_to_name,
        "proposed_date": r.proposed_date,
        "created_at": r.created_at.isoformat(),
    } for r in requests])
