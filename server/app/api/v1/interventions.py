"""
app.api.v1.interventions — Teacher Intervention Management Endpoints
"""

from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, status

from app.api.deps import (
    CurrentUser,
    PaginationParams,
    get_current_user,
    get_pagination,
    require_school_access,
)
from app.schemas.intervention import (
    InterventionCreate,
    InterventionResponse,
    InterventionUpdate,
)
from app.services.class_service import ClassService
from app.services.intervention_service import InterventionService
from app.services.student_service import StudentService
from app.utils.responses import error_response, success_response

router = APIRouter(tags=["Interventions"])


@router.post("", summary="Create a new student intervention")
async def create_intervention(
    payload: InterventionCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    require_school_access(payload.school_id, current_user)
    
    student = StudentService.get_student(payload.student_id)
    if not student:
        return error_response(code="STUDENT_NOT_FOUND", message="Student not found.", status_code=status.HTTP_404_NOT_FOUND)

    intervention = InterventionService.create_intervention(payload, teacher_id=current_user.uid)
    return success_response(
        data=InterventionResponse.from_model(intervention).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/{intervention_id}", summary="Get intervention details")
async def get_intervention(
    intervention_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    intervention = InterventionService.get_intervention(intervention_id)
    if not intervention:
        return error_response(code="INTERVENTION_NOT_FOUND", message="Intervention not found.", status_code=status.HTTP_404_NOT_FOUND)

    require_school_access(intervention.school_id, current_user)
    return success_response(data=InterventionResponse.from_model(intervention).model_dump())


@router.patch("/{intervention_id}", summary="Update intervention status or outcome")
async def update_intervention(
    intervention_id: str,
    payload: InterventionUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    intervention = InterventionService.get_intervention(intervention_id)
    if not intervention:
        return error_response(code="INTERVENTION_NOT_FOUND", message="Intervention not found.", status_code=status.HTTP_404_NOT_FOUND)

    require_school_access(intervention.school_id, current_user)
    updated = InterventionService.update_intervention(intervention_id, payload)
    return success_response(data=InterventionResponse.from_model(updated).model_dump())


@router.get("/student/{student_id}", summary="List interventions for a student")
async def list_student_interventions(
    student_id: str,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: CurrentUser = Depends(get_current_user),
):
    student = StudentService.get_student(student_id)
    if not student:
        return error_response(code="STUDENT_NOT_FOUND", message="Student not found.", status_code=status.HTTP_404_NOT_FOUND)

    require_school_access(student.school_id, current_user)
    interventions = InterventionService.list_student_interventions(student_id, skip=pagination.skip, limit=pagination.limit)
    data = [InterventionResponse.from_model(i).model_dump() for i in interventions]
    return success_response(data=data)


@router.get("/class/{class_id}", summary="List interventions for a class")
async def list_class_interventions(
    class_id: str,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: CurrentUser = Depends(get_current_user),
):
    class_obj = ClassService.get_class(class_id)
    if not class_obj:
        return error_response(code="CLASS_NOT_FOUND", message="Class not found.", status_code=status.HTTP_404_NOT_FOUND)

    require_school_access(class_obj.school_id, current_user)
    interventions = InterventionService.list_class_interventions(class_id, skip=pagination.skip, limit=pagination.limit)
    data = [InterventionResponse.from_model(i).model_dump() for i in interventions]
    return success_response(data=data)


@router.get("/school/{school_id}", summary="List all interventions for a school")
async def list_school_interventions(
    school_id: str,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: CurrentUser = Depends(get_current_user),
):
    require_school_access(school_id, current_user)
    interventions = InterventionService.list_school_interventions(school_id, skip=pagination.skip, limit=pagination.limit)
    data = [InterventionResponse.from_model(i).model_dump() for i in interventions]
    return success_response(data=data)
