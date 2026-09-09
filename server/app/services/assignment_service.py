"""
app.services.assignment_service — Assignment & Submission Business Logic
"""

from __future__ import annotations

import datetime as dt_mod
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.core.firebase import get_firestore_client
from app.models.academic import HomeworkStatus
from app.models.assignment import (
    Assignment,
    AssignmentStatus,
    AssignmentSubmission,
    SubmissionStatus,
)
from app.schemas.academic import HomeworkCreate
from app.services.class_service import ClassService
from app.services.homework_service import HomeworkService
from app.services.student_service import StudentService


class AssignmentService:

    @staticmethod
    def _assignments_col():
        return get_firestore_client().collection("assignments")

    @staticmethod
    def _submissions_col(assignment_id: str):
        return get_firestore_client().collection("assignments").document(assignment_id).collection("submissions")

    # ---------------------------------------------------------------------------
    # Assignment CRUD
    # ---------------------------------------------------------------------------

    @classmethod
    def create_assignment(
        cls,
        school_id: str,
        class_id: str,
        teacher_id: str,
        teacher_name: str,
        title: str,
        subject: str,
        due_date: str,
        due_time: str = "23:59",
        max_marks: float = 20.0,
        description: str = "",
        attachments: Optional[List[Dict[str, Any]]] = None,
        status: AssignmentStatus = AssignmentStatus.PUBLISHED,
    ) -> Assignment:
        assignment_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc)
        assignment = Assignment(
            id=assignment_id,
            school_id=school_id,
            class_id=class_id,
            teacher_id=teacher_id,
            teacher_name=teacher_name,
            title=title,
            subject=subject,
            description=description,
            due_date=due_date,
            due_time=due_time or "23:59",
            max_marks=max_marks,
            attachments=attachments or [],
            status=status,
            created_at=now,
            updated_at=now,
        )
        cls._assignments_col().document(assignment_id).set(assignment.to_firestore())
        return assignment

    @classmethod
    def get_assignment(cls, assignment_id: str) -> Optional[Assignment]:
        doc = cls._assignments_col().document(assignment_id).get()
        if not doc.exists:
            return None
        return Assignment.from_firestore(doc.id, doc.to_dict())

    @classmethod
    def update_assignment(cls, assignment_id: str, updates: dict) -> Optional[Assignment]:
        doc_ref = cls._assignments_col().document(assignment_id)
        doc = doc_ref.get()
        if not doc.exists:
            return None

        clean_updates = {k: v for k, v in updates.items() if v is not None}
        clean_updates["updated_at"] = datetime.now(tz=timezone.utc)
        if "status" in clean_updates and hasattr(clean_updates["status"], "value"):
            clean_updates["status"] = clean_updates["status"].value

        doc_ref.update(clean_updates)
        updated_doc = doc_ref.get()
        return Assignment.from_firestore(updated_doc.id, updated_doc.to_dict())

    @classmethod
    def delete_assignment(cls, assignment_id: str) -> bool:
        doc_ref = cls._assignments_col().document(assignment_id)
        if not doc_ref.get().exists:
            return False

        # Delete subcollection docs
        for sub_doc in cls._submissions_col(assignment_id).stream():
            sub_doc.reference.delete()

        doc_ref.delete()
        return True

    @classmethod
    def list_class_assignments(cls, class_id: str) -> List[Assignment]:
        docs = cls._assignments_col().where("class_id", "==", class_id).stream()
        assignments = [Assignment.from_firestore(d.id, d.to_dict()) for d in docs]
        assignments.sort(key=lambda a: (a.due_date, a.due_time))
        return assignments

    @classmethod
    def list_teacher_assignments(cls, teacher_id: str, school_id: str) -> List[Assignment]:
        docs = (
            cls._assignments_col()
            .where("school_id", "==", school_id)
            .where("teacher_id", "==", teacher_id)
            .stream()
        )
        assignments = [Assignment.from_firestore(d.id, d.to_dict()) for d in docs]
        assignments.sort(key=lambda a: (a.due_date, a.due_time), reverse=True)
        return assignments

    @classmethod
    def list_school_assignments(cls, school_id: str) -> List[Assignment]:
        docs = cls._assignments_col().where("school_id", "==", school_id).stream()
        assignments = [Assignment.from_firestore(d.id, d.to_dict()) for d in docs]
        assignments.sort(key=lambda a: (a.due_date, a.due_time), reverse=True)
        return assignments

    # ---------------------------------------------------------------------------
    # Assignment Metrics & Submissions
    # ---------------------------------------------------------------------------

    @classmethod
    def get_assignment_metrics(cls, assignment_id: str, class_id: str) -> Tuple[int, int, int, int]:
        """Returns (total_students, submitted_count, graded_count, late_count)."""
        students = StudentService.list_class_students(class_id, limit=200)
        total_students = len(students)

        subs = cls.list_all_submissions(assignment_id)
        submitted_count = len(subs)
        graded_count = sum(1 for s in subs if s.status == SubmissionStatus.GRADED)
        late_count = sum(1 for s in subs if s.is_late)

        return total_students, submitted_count, graded_count, late_count

    @classmethod
    def list_all_submissions(cls, assignment_id: str) -> List[AssignmentSubmission]:
        docs = cls._submissions_col(assignment_id).stream()
        return [AssignmentSubmission.from_firestore(d.id, d.to_dict()) for d in docs]

    @classmethod
    def get_submission(cls, assignment_id: str, student_id: str) -> Optional[AssignmentSubmission]:
        sub_id = AssignmentSubmission.make_id(assignment_id, student_id)
        doc = cls._submissions_col(assignment_id).document(sub_id).get()
        if not doc.exists:
            return None
        return AssignmentSubmission.from_firestore(doc.id, doc.to_dict())

    @classmethod
    def submit_assignment(
        cls,
        assignment_id: str,
        student_id: str,
        content: Optional[str] = None,
        attachment_name: Optional[str] = None,
        attachment_url: Optional[str] = None,
    ) -> AssignmentSubmission:
        assignment = cls.get_assignment(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")

        student = StudentService.get_student(student_id)
        if not student:
            raise ValueError("Student not found")

        now = datetime.now(tz=timezone.utc)
        today_date_str = now.strftime("%Y-%m-%d")
        now_time_str = now.strftime("%H:%M")

        # Determine if submission is late
        is_late = False
        if today_date_str > assignment.due_date:
            is_late = True
        elif today_date_str == assignment.due_date and now_time_str > assignment.due_time:
            is_late = True

        sub_id = AssignmentSubmission.make_id(assignment_id, student_id)
        existing = cls.get_submission(assignment_id, student_id)

        status = SubmissionStatus.LATE if is_late else SubmissionStatus.SUBMITTED
        # If already graded, keep graded or preserve feedback
        obtained_marks = existing.obtained_marks if existing else None
        feedback = existing.feedback if existing else None
        graded_by = existing.graded_by if existing else None
        graded_at = existing.graded_at if existing else None
        if existing and existing.status == SubmissionStatus.GRADED:
            status = SubmissionStatus.GRADED

        sub = AssignmentSubmission(
            id=sub_id,
            assignment_id=assignment_id,
            school_id=assignment.school_id,
            class_id=assignment.class_id,
            student_id=student.id,
            student_name=student.name,
            student_code=student.student_code,
            submitted_at=now,
            content=content,
            attachment_name=attachment_name,
            attachment_url=attachment_url,
            status=status,
            is_late=is_late,
            obtained_marks=obtained_marks,
            feedback=feedback,
            graded_by=graded_by,
            graded_at=graded_at,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )

        cls._submissions_col(assignment_id).document(sub_id).set(sub.to_firestore())

        # Automatically bridge with HomeworkRecord to feed AI Risk Engine
        try:
            hw_status = HomeworkStatus.LATE if is_late else HomeworkStatus.SUBMITTED
            HomeworkService.record_homework(
                HomeworkCreate(
                    student_id=student.id,
                    school_id=assignment.school_id,
                    class_id=assignment.class_id,
                    assignment_id=assignment.id,
                    assignment_date=assignment.due_date,
                    status=hw_status,
                    source="classwork",
                )
            )
        except Exception:
            pass  # Best effort sync without blocking submission

        return sub

    @classmethod
    def grade_submission(
        cls,
        assignment_id: str,
        student_id: str,
        obtained_marks: float,
        feedback: Optional[str] = None,
        teacher_id: Optional[str] = None,
    ) -> AssignmentSubmission:
        assignment = cls.get_assignment(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")

        if obtained_marks < 0:
            raise ValueError("Marks cannot be negative")
        if obtained_marks > assignment.max_marks:
            raise ValueError(f"Marks cannot exceed maximum marks ({assignment.max_marks})")

        sub = cls.get_submission(assignment_id, student_id)
        now = datetime.now(tz=timezone.utc)

        if not sub:
            # Teacher is grading a student who hasn't submitted yet (or manual paper grade)
            student = StudentService.get_student(student_id)
            if not student:
                raise ValueError("Student not found")
            sub_id = AssignmentSubmission.make_id(assignment_id, student_id)
            sub = AssignmentSubmission(
                id=sub_id,
                assignment_id=assignment_id,
                school_id=assignment.school_id,
                class_id=assignment.class_id,
                student_id=student.id,
                student_name=student.name,
                student_code=student.student_code,
                submitted_at=now,
                status=SubmissionStatus.GRADED,
                is_late=False,
                obtained_marks=obtained_marks,
                feedback=feedback,
                graded_by=teacher_id,
                graded_at=now,
                created_at=now,
                updated_at=now,
            )
        else:
            sub.obtained_marks = obtained_marks
            sub.feedback = feedback
            sub.status = SubmissionStatus.GRADED
            sub.graded_by = teacher_id
            sub.graded_at = now
            sub.updated_at = now

        cls._submissions_col(assignment_id).document(sub.id).set(sub.to_firestore())
        return sub

    @classmethod
    def list_assignment_submissions(cls, assignment_id: str, class_id: str) -> List[dict]:
        """Returns full class roster merged with existing submission records."""
        students = StudentService.list_class_students(class_id, limit=200)
        existing_subs = {s.student_id: s for s in cls.list_all_submissions(assignment_id)}

        roster = []
        for stu in sorted(students, key=lambda s: s.student_code):
            sub = existing_subs.get(stu.id)
            roster.append({
                "student_id": stu.id,
                "student_name": stu.name,
                "student_code": stu.student_code,
                "submission_id": sub.id if sub else None,
                "status": sub.status.value if sub else "NOT_SUBMITTED",
                "submitted_at": sub.submitted_at.isoformat() if sub and sub.submitted_at else None,
                "is_late": sub.is_late if sub else False,
                "content": sub.content if sub else None,
                "attachment_name": sub.attachment_name if sub else None,
                "attachment_url": sub.attachment_url if sub else None,
                "obtained_marks": sub.obtained_marks if sub else None,
                "feedback": sub.feedback if sub else None,
                "graded_by": sub.graded_by if sub else None,
                "graded_at": sub.graded_at.isoformat() if sub and sub.graded_at else None,
            })
        return roster

    @classmethod
    def get_student_assignments(cls, student_id: str, class_id: str) -> List[dict]:
        """Returns all assignments for the student's class annotated with student's submission status."""
        assignments = cls.list_class_assignments(class_id)
        today = dt_mod.date.today()

        results = []
        for a in assignments:
            sub = cls.get_submission(a.id, student_id)
            due_date_obj = dt_mod.date.fromisoformat(a.due_date)
            days_remaining = (due_date_obj - today).days

            # Determine student-facing urgency category
            is_submitted = sub is not None and sub.status in (
                SubmissionStatus.SUBMITTED,
                SubmissionStatus.LATE,
                SubmissionStatus.GRADED,
            )
            is_graded = sub is not None and sub.status == SubmissionStatus.GRADED

            if is_submitted:
                urgency = "COMPLETED"
            elif days_remaining < 0:
                urgency = "OVERDUE"
            elif days_remaining == 0:
                urgency = "DUE_TODAY"
            elif days_remaining == 1:
                urgency = "DUE_TOMORROW"
            elif days_remaining <= 7:
                urgency = "THIS_WEEK"
            else:
                urgency = "UPCOMING"

            results.append({
                "assignment": a.model_dump(mode="json"),
                "submission": sub.model_dump(mode="json") if sub else None,
                "urgency": urgency,
                "days_remaining": days_remaining,
                "is_submitted": is_submitted,
                "is_graded": is_graded,
            })

        return results

    # ---------------------------------------------------------------------------
    # Principal Analytics
    # ---------------------------------------------------------------------------

    @classmethod
    def get_school_assignment_stats(cls, school_id: str) -> dict:
        classes = ClassService.list_school_classes(school_id)
        all_assignments = cls.list_school_assignments(school_id)

        class_stats_list = []
        total_assignments = len(all_assignments)
        total_submissions_count = 0
        total_graded_count = 0
        total_potential_submissions = 0

        for c in classes:
            class_assigns = [a for a in all_assignments if a.class_id == c.id]
            students = StudentService.list_class_students(c.id, limit=200)
            stu_count = len(students)

            cls_subs = 0
            cls_graded = 0
            cls_late = 0

            for a in class_assigns:
                subs = cls.list_all_submissions(a.id)
                cls_subs += len(subs)
                cls_graded += sum(1 for s in subs if s.status == SubmissionStatus.GRADED)
                cls_late += sum(1 for s in subs if s.is_late)

            potential = len(class_assigns) * stu_count
            total_potential_submissions += potential
            total_submissions_count += cls_subs
            total_graded_count += cls_graded

            submission_rate = round((cls_subs / potential * 100), 1) if potential > 0 else 0.0

            class_stats_list.append({
                "class_id": c.id,
                "class_name": f"Class {c.grade}-{c.section}",
                "total_assignments": len(class_assigns),
                "total_students": stu_count,
                "total_submissions": cls_subs,
                "submission_rate": submission_rate,
                "late_submissions": cls_late,
                "pending_submissions": max(0, potential - cls_subs),
                "graded_submissions": cls_graded,
            })

        overall_sub_rate = (
            round((total_submissions_count / total_potential_submissions * 100), 1)
            if total_potential_submissions > 0
            else 0.0
        )

        return {
            "total_assignments": total_assignments,
            "total_submissions": total_submissions_count,
            "total_graded": total_graded_count,
            "overall_submission_rate": overall_sub_rate,
            "classes": class_stats_list,
        }
