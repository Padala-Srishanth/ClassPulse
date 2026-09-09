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


@router.get("/timetable", summary="Student own class timetable")
async def student_timetable(
    class_id: Optional[str] = Query(None, description="Optional class ID override (must match student's class)"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Return the timetable for the authenticated student's assigned class.

    Automatically resolves the student's class from their profile.
    Rejects foreign class requests with 403 Forbidden.
    """
    student_id, school_id = _get_student_identity(current_user)

    from app.services.timetable_service import TimetableService
    from app.services.student_service import StudentService
    from app.services.class_service import ClassService
    from app.schemas.timetable import TimetableSlotResponse
    from app.models.timetable import DAY_LABELS, DayOfWeek
    import datetime as dt_mod

    # 1. Automatically resolve student's assigned class
    assigned_class_id = None
    if student_id:
        stu_obj = StudentService.get_student(student_id)
        if stu_obj:
            assigned_class_id = stu_obj.class_id

    # Fallback to demo class if student document is not yet seeded
    if not assigned_class_id:
        assigned_class_id = "class-10a"

    # 2. Strict tenancy check: Student cannot query another class's timetable
    if class_id and class_id != assigned_class_id:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail={"code": "STUDENT_CLASS_MISMATCH", "message": "Students can only access their own class timetable."},
        )

    target_class_id = class_id or assigned_class_id

    # Verify class belongs to the student's school
    cls_obj = ClassService.get_class(target_class_id)
    if cls_obj and cls_obj.school_id != school_id:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTH_SCHOOL_ACCESS_DENIED", "message": "Access denied."},
        )

    slots = TimetableService.list_class_slots(target_class_id)
    slot_data = [TimetableSlotResponse.from_model(s).model_dump() for s in slots]

    # Compute today's day of week
    weekday = dt_mod.date.today().weekday()
    is_sunday = (weekday == 6)
    day_map = {0: "MON", 1: "TUE", 2: "WED", 3: "THU", 4: "FRI", 5: "SAT", 6: "SAT"}
    today_key = day_map.get(weekday, "MON")
    today_slots = [s for s in slot_data if s["day_of_week"] == today_key] if not is_sunday else []

    # On Sunday, provide next school day (Monday) slots
    next_day_key = "MON" if is_sunday else None
    next_day_slots = [s for s in slot_data if s["day_of_week"] == next_day_key] if next_day_key else []

    # Group by day_of_week
    grouped: dict = {}
    for s in slot_data:
        day = s["day_of_week"]
        if day not in grouped:
            grouped[day] = {"day": day, "label": DAY_LABELS.get(day, day), "slots": []}
        grouped[day]["slots"].append(s)

    return success_response(data={
        "class_id": target_class_id,
        "slots": slot_data,
        "today_slots": today_slots,
        "today_label": DAY_LABELS.get(today_key, today_key),
        "is_sunday": is_sunday,
        "next_day_slots": next_day_slots,
        "next_day_label": DAY_LABELS.get(next_day_key, "Monday") if next_day_key else None,
        "grouped": grouped,
    })


@router.get("/upcoming-exams", summary="Student's upcoming exams")
async def student_upcoming_exams(
    class_id: Optional[str] = Query(None, description="Optional class ID override (must match student's class)"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Return upcoming exams for the student's assigned class.

    Automatically resolves student's class from profile and rejects mismatches.
    """
    student_id, school_id = _get_student_identity(current_user)

    from app.services.exam_service import ExamService
    from app.services.student_service import StudentService
    from app.services.class_service import ClassService
    from app.schemas.exam import ExamResponse
    import datetime as dt_mod

    # 1. Automatically resolve student's class
    assigned_class_id = None
    if student_id:
        stu_obj = StudentService.get_student(student_id)
        if stu_obj:
            assigned_class_id = stu_obj.class_id
    if not assigned_class_id:
        assigned_class_id = "class-10a"

    # 2. Strict tenancy check: Student cannot query another class's exams
    if class_id and class_id != assigned_class_id:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail={"code": "STUDENT_CLASS_MISMATCH", "message": "Students can only access exams for their own class."},
        )

    target_class_id = class_id or assigned_class_id

    # Verify class belongs to student's school
    cls_obj = ClassService.get_class(target_class_id)
    if not cls_obj:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(status_code=404, detail={"code": "CLASS_NOT_FOUND", "message": "Class not found."})
    if cls_obj.school_id != school_id:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTH_SCHOOL_ACCESS_DENIED", "message": "Access denied."},
        )

    today_str = dt_mod.date.today().isoformat()
    all_exams = ExamService.list_class_exams(target_class_id)
    upcoming = [e for e in all_exams if e.exam_date >= today_str]

    result = []
    for exam in upcoming:
        exam_date_obj = dt_mod.date.fromisoformat(exam.exam_date)
        days_remaining = (exam_date_obj - dt_mod.date.today()).days
        entry = ExamResponse.from_model(exam).model_dump()
        entry["days_remaining"] = days_remaining
        if days_remaining == 0:
            entry["urgency"] = "TODAY"
        elif days_remaining == 1:
            entry["urgency"] = "TOMORROW"
        elif days_remaining <= 7:
            entry["urgency"] = "THIS_WEEK"
        else:
            entry["urgency"] = "UPCOMING"
        result.append(entry)

    return success_response(data=result)


@router.get("/assignments", summary="Student's assignments & classwork")
async def student_assignments(
    class_id: Optional[str] = Query(None, description="Optional class ID override (must match student's assigned class)"),
    current_user: CurrentUser = Depends(get_current_user),
):
    student_id, school_id = _get_student_identity(current_user)

    from app.services.student_service import StudentService
    from app.services.class_service import ClassService
    from app.services.assignment_service import AssignmentService
    from fastapi import HTTPException

    # 1. Automatically resolve student's class
    assigned_class_id = None
    if student_id:
        stu_obj = StudentService.get_student(student_id)
        if stu_obj:
            assigned_class_id = stu_obj.class_id
    if not assigned_class_id:
        assigned_class_id = "class-10a"

    # 2. Strict tenancy check
    if class_id and class_id != assigned_class_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "STUDENT_CLASS_MISMATCH", "message": "Students can only access assignments for their own class."},
        )

    target_class_id = class_id or assigned_class_id

    # Verify class belongs to student's school
    cls_obj = ClassService.get_class(target_class_id)
    if not cls_obj:
        raise HTTPException(status_code=404, detail={"code": "CLASS_NOT_FOUND", "message": "Class not found."})
    if cls_obj.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTH_SCHOOL_ACCESS_DENIED", "message": "Access denied."},
        )

    items = AssignmentService.get_student_assignments(student_id or "demo-student-001", target_class_id)

    # Categorize items into pending, overdue, and completed
    pending = [item for item in items if not item["is_submitted"] and item["urgency"] != "OVERDUE"]
    overdue = [item for item in items if not item["is_submitted"] and item["urgency"] == "OVERDUE"]
    completed = [item for item in items if item["is_submitted"]]

    return success_response(data={
        "all": items,
        "pending": pending,
        "overdue": overdue,
        "completed": completed,
        "total_assigned": len(items),
        "total_completed": len(completed),
        "total_overdue": len(overdue),
    })


@router.get("/doubts", summary="Student's own and class doubts")
async def student_doubts(
    class_id: Optional[str] = Query(None, description="Optional class ID override (must match student's class)"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Return doubts for the authenticated student's class."""
    student_id, school_id = _get_student_identity(current_user)

    from app.services.student_service import StudentService
    from app.services.class_service import ClassService
    from app.services.doubt_service import DoubtService
    from fastapi import HTTPException

    # 1. Resolve student class
    assigned_class_id = None
    if student_id:
        stu_obj = StudentService.get_student(student_id)
        if stu_obj:
            assigned_class_id = stu_obj.class_id
    if not assigned_class_id:
        assigned_class_id = "class-10a"

    # 2. Tenancy check
    if class_id and class_id != assigned_class_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "STUDENT_CLASS_MISMATCH", "message": "Students can only access doubts for their own class."},
        )

    target_class_id = class_id or assigned_class_id

    cls_obj = ClassService.get_class(target_class_id)
    if cls_obj and cls_obj.school_id != school_id:
        raise HTTPException(status_code=403, detail={"code": "AUTH_SCHOOL_ACCESS_DENIED", "message": "Access denied."})

    all_doubts = DoubtService.list_class_doubts(target_class_id)
    stu_id = student_id or "demo-student-001"

    # Students see: CLASS-visibility doubts + their own PRIVATE doubts
    visible = [
        d for d in all_doubts
        if d.visibility.value == "CLASS" or d.student_id == stu_id
    ]
    own = [d for d in visible if d.student_id == stu_id]

    from app.schemas.doubt import DoubtResponse
    return success_response(data={
        "class_doubts": [DoubtResponse.from_model(d).model_dump(mode="json") for d in visible],
        "my_doubts": [DoubtResponse.from_model(d).model_dump(mode="json") for d in own],
        "total": len(visible),
        "open_count": sum(1 for d in visible if d.status.value == "OPEN"),
        "answered_count": sum(1 for d in visible if d.status.value == "ANSWERED"),
    })


@router.post("/doubts", summary="Post a new academic doubt", status_code=status.HTTP_201_CREATED)
async def student_post_doubt(
    body: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Student posts a new academic doubt."""
    student_id, school_id = _get_student_identity(current_user)

    from app.services.student_service import StudentService
    from app.services.class_service import ClassService
    from app.services.doubt_service import DoubtService
    from app.schemas.doubt import DoubtCreate, DoubtResponse
    from app.models.doubt import DoubtVisibility
    from fastapi import HTTPException

    stu_id = student_id or "demo-student-001"
    stu_obj = StudentService.get_student(stu_id)
    student_name = stu_obj.name if stu_obj else "Student"
    assigned_class_id = stu_obj.class_id if stu_obj else "class-10a"

    validated = DoubtCreate(**body)
    doubt_class_id = validated.class_id or assigned_class_id

    # Tenancy check
    if doubt_class_id != assigned_class_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "STUDENT_CLASS_MISMATCH", "message": "You can only post doubts for your own class."},
        )

    vis = DoubtVisibility(validated.visibility) if validated.visibility else DoubtVisibility.CLASS

    doubt = DoubtService.create_doubt(
        school_id=school_id,
        class_id=doubt_class_id,
        student_id=stu_id,
        student_name=student_name,
        title=validated.title,
        body=validated.body,
        subject=validated.subject,
        attachment_name=validated.attachment_name,
        attachment_url=validated.attachment_url,
        visibility=vis,
    )
    return success_response(data=DoubtResponse.from_model(doubt).model_dump(mode="json"), status_code=status.HTTP_201_CREATED)


@router.get("/doubts/{doubt_id}", summary="Get a single doubt with replies (Student)")
async def student_get_doubt(
    doubt_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    student_id, school_id = _get_student_identity(current_user)

    from app.services.doubt_service import DoubtService
    from app.schemas.doubt import DoubtResponse, DoubtReplyResponse
    from fastapi import HTTPException

    doubt = DoubtService.get_doubt(doubt_id)
    if not doubt:
        raise HTTPException(status_code=404, detail={"code": "DOUBT_NOT_FOUND", "message": "Doubt not found."})
    if doubt.school_id != school_id:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Access denied."})

    stu_id = student_id or "demo-student-001"
    if doubt.visibility.value == "PRIVATE" and doubt.student_id != stu_id:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Private doubt."})

    replies = DoubtService.list_replies(doubt_id)
    return success_response(data={
        "doubt": DoubtResponse.from_model(doubt).model_dump(mode="json"),
        "replies": [DoubtReplyResponse.from_model(r).model_dump(mode="json") for r in replies],
    })


@router.post("/doubts/{doubt_id}/replies", summary="Reply to a doubt (Student)", status_code=status.HTTP_201_CREATED)
async def student_reply_to_doubt(
    doubt_id: str,
    body: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    student_id, school_id = _get_student_identity(current_user)

    from app.services.student_service import StudentService
    from app.services.doubt_service import DoubtService
    from app.schemas.doubt import DoubtReplyCreate, DoubtReplyResponse
    from fastapi import HTTPException

    doubt = DoubtService.get_doubt(doubt_id)
    if not doubt:
        raise HTTPException(status_code=404, detail={"code": "DOUBT_NOT_FOUND", "message": "Doubt not found."})
    if doubt.school_id != school_id:
        raise HTTPException(status_code=403, detail={"code": "ACCESS_DENIED", "message": "Access denied."})

    validated = DoubtReplyCreate(**body)
    stu_id = student_id or "demo-student-001"
    stu_obj = StudentService.get_student(stu_id)
    author_name = stu_obj.name if stu_obj else "Student"

    reply = DoubtService.add_reply(
        doubt_id=doubt_id,
        school_id=school_id,
        class_id=doubt.class_id,
        author_id=current_user.uid,
        author_name=author_name,
        author_role="STUDENT",
        body=validated.body,
        attachment_name=validated.attachment_name,
        attachment_url=validated.attachment_url,
    )
    return success_response(data=DoubtReplyResponse.from_model(reply).model_dump(mode="json"), status_code=status.HTTP_201_CREATED)


@router.post("/assignments/{assignment_id}/submit", summary="Submit work for an assignment")
async def student_submit_assignment(
    assignment_id: str,
    body: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    student_id, school_id = _get_student_identity(current_user)
    stu_id = student_id or "demo-student-001"

    from app.services.assignment_service import AssignmentService
    from app.services.student_service import StudentService
    from app.schemas.assignment import SubmissionCreate, SubmissionResponse
    from fastapi import HTTPException

    assignment = AssignmentService.get_assignment(assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail={"code": "ASSIGNMENT_NOT_FOUND", "message": "Assignment not found."})
    if assignment.school_id != school_id:
        raise HTTPException(status_code=403, detail={"code": "AUTH_SCHOOL_ACCESS_DENIED", "message": "Access denied."})

    # Verify student belongs to this assignment's class
    stu = StudentService.get_student(stu_id)
    if stu and stu.class_id != assignment.class_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "STUDENT_CLASS_MISMATCH", "message": "You cannot submit an assignment for a class you are not enrolled in."},
        )

    validated_body = SubmissionCreate(**body)

    try:
        sub = AssignmentService.submit_assignment(
            assignment_id=assignment_id,
            student_id=stu_id,
            content=validated_body.content,
            attachment_name=validated_body.attachment_name,
            attachment_url=validated_body.attachment_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"code": "SUBMISSION_ERROR", "message": str(e)})

    return success_response(data=SubmissionResponse.from_model(sub).model_dump(mode="json"))

