"""
app.schemas.assignment — Pydantic Validation Schemas for Assignments & Submissions
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.assignment import Assignment, AssignmentStatus, AssignmentSubmission, SubmissionStatus


class AssignmentCreate(BaseModel):
    class_id: str
    title: str = Field(..., min_length=2, max_length=150)
    subject: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = ""
    due_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    due_time: Optional[str] = Field("23:59", pattern=r"^\d{2}:\d{2}$")  # HH:MM
    max_marks: float = Field(20.0, gt=0, le=1000)
    attachments: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    due_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    max_marks: Optional[float] = Field(None, gt=0, le=1000)
    status: Optional[AssignmentStatus] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class SubmissionCreate(BaseModel):
    content: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_url: Optional[str] = None


class SubmissionGradeUpdate(BaseModel):
    obtained_marks: float = Field(..., ge=0)
    feedback: Optional[str] = None


class SubmissionResponse(BaseModel):
    id: str
    assignment_id: str
    school_id: str
    class_id: str
    student_id: str
    student_name: str
    student_code: str
    submitted_at: Optional[datetime] = None
    content: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_url: Optional[str] = None
    status: SubmissionStatus
    is_late: bool
    obtained_marks: Optional[float] = None
    feedback: Optional[str] = None
    graded_by: Optional[str] = None
    graded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, sub: AssignmentSubmission) -> "SubmissionResponse":
        return cls(
            id=sub.id,
            assignment_id=sub.assignment_id,
            school_id=sub.school_id,
            class_id=sub.class_id,
            student_id=sub.student_id,
            student_name=sub.student_name,
            student_code=sub.student_code,
            submitted_at=sub.submitted_at,
            content=sub.content,
            attachment_name=sub.attachment_name,
            attachment_url=sub.attachment_url,
            status=sub.status,
            is_late=sub.is_late,
            obtained_marks=sub.obtained_marks,
            feedback=sub.feedback,
            graded_by=sub.graded_by,
            graded_at=sub.graded_at,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
        )


class AssignmentResponse(BaseModel):
    id: str
    school_id: str
    class_id: str
    teacher_id: str
    teacher_name: str
    title: str
    subject: str
    description: str
    due_date: str
    due_time: str
    max_marks: float
    attachments: List[Dict[str, Any]]
    status: AssignmentStatus
    created_at: datetime
    updated_at: datetime

    # Summary metrics for teachers & principal
    total_students: int = 0
    submitted_count: int = 0
    graded_count: int = 0
    late_count: int = 0

    @classmethod
    def from_model(
        cls,
        assignment: Assignment,
        total_students: int = 0,
        submitted_count: int = 0,
        graded_count: int = 0,
        late_count: int = 0,
    ) -> "AssignmentResponse":
        return cls(
            id=assignment.id,
            school_id=assignment.school_id,
            class_id=assignment.class_id,
            teacher_id=assignment.teacher_id,
            teacher_name=assignment.teacher_name,
            title=assignment.title,
            subject=assignment.subject,
            description=assignment.description,
            due_date=assignment.due_date,
            due_time=assignment.due_time,
            max_marks=assignment.max_marks,
            attachments=assignment.attachments,
            status=assignment.status,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
            total_students=total_students,
            submitted_count=submitted_count,
            graded_count=graded_count,
            late_count=late_count,
        )


class StudentAssignmentItem(BaseModel):
    """Assignment details joined with the student's individual submission state."""
    assignment: AssignmentResponse
    submission: Optional[SubmissionResponse] = None
    urgency: str = "UPCOMING"  # "DUE_TODAY" | "DUE_TOMORROW" | "THIS_WEEK" | "UPCOMING" | "OVERDUE"
    days_remaining: int = 0
    is_submitted: bool = False
    is_graded: bool = False


class ClassAssignmentStats(BaseModel):
    class_id: str
    class_name: str
    total_assignments: int
    total_students: int
    total_submissions: int
    submission_rate: float
    late_submissions: int
    pending_submissions: int
    graded_submissions: int


class SchoolAssignmentStatsResponse(BaseModel):
    total_assignments: int
    total_submissions: int
    total_graded: int
    overall_submission_rate: float
    classes: List[ClassAssignmentStats]
