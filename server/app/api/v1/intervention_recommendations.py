"""
app.api.v1.intervention_recommendations — Smart Intervention Recommendation Endpoints
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    CurrentUser,
    get_current_user,
    require_school_access,
)
from app.models.intervention_recommendation import DismissalReason
from app.schemas.intervention_recommendation import (
    RecommendationApproveRequest,
    RecommendationDismissRequest,
    RecommendationResponse,
)
from app.services.class_service import ClassService
from app.services.intervention_recommendation_service import InterventionRecommendationService
from app.services.student_service import StudentService
from app.utils.responses import error_response, success_response

router = APIRouter(tags=["Intervention Recommendations"])


def _check_not_student(current_user: CurrentUser):
    if current_user.is_student:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "AUTH_INSUFFICIENT_ROLE",
                "message": "Students are not permitted to access intervention recommendations.",
            },
        )


# =============================================================================
# 1. Student-Scoped Endpoints
# =============================================================================

@router.post(
    "/student/{student_id}/analyze",
    summary="Analyze student and generate/refresh smart intervention recommendations",
)
async def analyze_student_recommendations(
    student_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    _check_not_student(current_user)
    student = StudentService.get_student(student_id)
    if not student:
        return error_response(
            code="STUDENT_NOT_FOUND",
            message="Student not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    require_school_access(student.school_id, current_user)

    recs = InterventionRecommendationService.analyze_student(student_id)
    data = [RecommendationResponse.from_model(r).model_dump(mode="json") for r in recs]
    return success_response(data=data, status_code=status.HTTP_200_OK)


@router.get(
    "/student/{student_id}",
    summary="Get recommendations for a student",
)
async def get_student_recommendations(
    student_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: CurrentUser = Depends(get_current_user),
):
    _check_not_student(current_user)
    student = StudentService.get_student(student_id)
    if not student:
        return error_response(
            code="STUDENT_NOT_FOUND",
            message="Student not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    require_school_access(student.school_id, current_user)

    recs = InterventionRecommendationService.get_student_recommendations(
        student_id=student_id, status_filter=status_filter
    )
    data = [RecommendationResponse.from_model(r).model_dump(mode="json") for r in recs]
    return success_response(data=data)


# =============================================================================
# 2. Class & School Scoped Endpoints
# =============================================================================

@router.get(
    "/class/{class_id}",
    summary="Get pending recommendations for a class cohort",
)
async def get_class_pending_recommendations(
    class_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    _check_not_student(current_user)
    class_obj = ClassService.get_class(class_id)
    if not class_obj:
        return error_response(
            code="CLASS_NOT_FOUND",
            message="Class not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    require_school_access(class_obj.school_id, current_user)

    recs = InterventionRecommendationService.get_pending_recommendations(class_id)
    data = [RecommendationResponse.from_model(r).model_dump(mode="json") for r in recs]
    return success_response(data=data)


@router.get(
    "/school/{school_id}",
    summary="Get school-wide recommendations (principal / school admin view)",
)
async def get_school_recommendations(
    school_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: CurrentUser = Depends(get_current_user),
):
    _check_not_student(current_user)
    require_school_access(school_id, current_user)

    recs = InterventionRecommendationService.get_school_recommendations(
        school_id=school_id, status_filter=status_filter
    )
    data = [RecommendationResponse.from_model(r).model_dump(mode="json") for r in recs]
    return success_response(data=data)


# =============================================================================
# 3. Action Endpoints: Approve & Dismiss (Dynamic ID routes declared last)
# =============================================================================

@router.post(
    "/{recommendation_id}/approve",
    summary="Approve recommendation and create intervention action plan",
)
async def approve_recommendation(
    recommendation_id: str,
    payload: Optional[RecommendationApproveRequest] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    _check_not_student(current_user)

    rec = InterventionRecommendationService.get_recommendation(recommendation_id)
    if not rec:
        return error_response(
            code="RECOMMENDATION_NOT_FOUND",
            message="Recommendation not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    require_school_access(rec.school_id, current_user)

    optional_type = payload.type if payload else None
    optional_notes = payload.notes if payload else None
    optional_follow_up = payload.follow_up_date if payload else None

    updated_rec, intervention = InterventionRecommendationService.approve_recommendation(
        recommendation_id=recommendation_id,
        user=current_user,
        optional_type=optional_type,
        optional_notes=optional_notes,
        optional_follow_up_date=optional_follow_up,
    )

    return success_response(
        data={
            "recommendation": RecommendationResponse.from_model(updated_rec).model_dump(mode="json"),
            "intervention_id": intervention.id,
        },
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/{recommendation_id}/dismiss",
    summary="Dismiss recommendation with educator reason",
)
async def dismiss_recommendation(
    recommendation_id: str,
    payload: Optional[RecommendationDismissRequest] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    _check_not_student(current_user)

    rec = InterventionRecommendationService.get_recommendation(recommendation_id)
    if not rec:
        return error_response(
            code="RECOMMENDATION_NOT_FOUND",
            message="Recommendation not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    require_school_access(rec.school_id, current_user)

    reason = payload.reason if payload else DismissalReason.TEACHER_JUDGMENT.value
    notes = payload.notes if payload else None

    updated_rec = InterventionRecommendationService.dismiss_recommendation(
        recommendation_id=recommendation_id,
        user=current_user,
        reason=reason,
        notes=notes,
    )

    return success_response(
        data=RecommendationResponse.from_model(updated_rec).model_dump(mode="json"),
        status_code=status.HTTP_200_OK,
    )
