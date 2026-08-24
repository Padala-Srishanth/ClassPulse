"""
app.api.v1.exams — Exam Management Endpoints

Teachers can create exams and enter marks.
Principal and Teachers can view results.
Percentages are always: obtained / max * 100 (never stored as raw %).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, get_current_user, require_school_access
from app.core.security import UserRole
from app.schemas.exam import BulkExamResultCreate, ExamCreate, ExamResponse, ExamResultResponse
from app.services.class_service import ClassService
from app.services.exam_service import ExamService
from app.utils.responses import error_response, success_response

router = APIRouter(tags=["Exams"])


def _require_teacher_or_above(user: CurrentUser) -> CurrentUser:
    if user.role not in {UserRole.ADMIN, UserRole.SCHOOL_ADMIN, UserRole.TEACHER}:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTH_INSUFFICIENT_ROLE", "message": "Teacher access required."},
        )
    return user


@router.post("", summary="Create a new exam")
async def create_exam(
    payload: ExamCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_teacher_or_above(current_user)
    require_school_access(payload.school_id, current_user)

    cls = ClassService.get_class(payload.class_id)
    if not cls or cls.school_id != payload.school_id:
        return error_response(code="CLASS_NOT_FOUND", message="Class not found.", status_code=404)

    exam = ExamService.create_exam(
        school_id=payload.school_id,
        class_id=payload.class_id,
        teacher_id=current_user.uid,
        exam_name=payload.exam_name,
        subject=payload.subject,
        exam_date=payload.exam_date,
        max_marks=payload.max_marks,
    )
    return success_response(
        data=ExamResponse.from_model(exam).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/{exam_id}", summary="Get exam details")
async def get_exam(
    exam_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_teacher_or_above(current_user)
    exam = ExamService.get_exam(exam_id)
    if not exam:
        return error_response(code="EXAM_NOT_FOUND", message="Exam not found.", status_code=404)
    require_school_access(exam.school_id, current_user)
    return success_response(data=ExamResponse.from_model(exam).model_dump())


@router.post("/{exam_id}/results", summary="Enter marks for multiple students")
async def enter_exam_results(
    exam_id: str,
    payload: BulkExamResultCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_teacher_or_above(current_user)
    exam = ExamService.get_exam(exam_id)
    if not exam:
        return error_response(code="EXAM_NOT_FOUND", message="Exam not found.", status_code=404)
    require_school_access(exam.school_id, current_user)

    results = []
    errors = []
    for entry in payload.results:
        if entry.obtained_marks > exam.max_marks:
            errors.append({
                "student_id": entry.student_id,
                "error": f"Obtained marks ({entry.obtained_marks}) exceed max marks ({exam.max_marks})",
            })
            continue
        result = ExamService.record_result(
            exam_id=exam_id,
            school_id=exam.school_id,
            class_id=exam.class_id,
            student_id=entry.student_id,
            obtained_marks=entry.obtained_marks,
            max_marks=exam.max_marks,
        )
        results.append(ExamResultResponse.from_model(result).model_dump())

    return success_response(data={"saved": results, "errors": errors})


@router.get("/{exam_id}/results", summary="Get all results for an exam")
async def get_exam_results(
    exam_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_teacher_or_above(current_user)
    exam = ExamService.get_exam(exam_id)
    if not exam:
        return error_response(code="EXAM_NOT_FOUND", message="Exam not found.", status_code=404)
    require_school_access(exam.school_id, current_user)

    results = ExamService.list_exam_results(exam_id)
    data = [ExamResultResponse.from_model(r).model_dump() for r in results]

    # Compute class statistics
    if data:
        percentages = [r["percentage"] for r in data]
        stats = {
            "count": len(data),
            "average_percentage": round(sum(percentages) / len(percentages), 1),
            "highest_percentage": round(max(percentages), 1),
            "lowest_percentage": round(min(percentages), 1),
            "pass_count": len([p for p in percentages if p >= 50]),
            "pass_percentage": round(len([p for p in percentages if p >= 50]) / len(percentages) * 100, 1),
        }
    else:
        stats = {"count": 0}

    return success_response(data={"exam": ExamResponse.from_model(exam).model_dump(), "results": data, "stats": stats})


@router.get("/class/{class_id}", summary="List exams for a class")
async def list_class_exams(
    class_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_teacher_or_above(current_user)
    cls = ClassService.get_class(class_id)
    if not cls:
        return error_response(code="CLASS_NOT_FOUND", message="Class not found.", status_code=404)
    require_school_access(cls.school_id, current_user)

    exams = ExamService.list_class_exams(class_id)
    return success_response(data=[ExamResponse.from_model(e).model_dump() for e in exams])
