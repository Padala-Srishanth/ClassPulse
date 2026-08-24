"""
app.services.exam_service — Exam & ExamResult Service
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.core.firebase import get_firestore_client
from app.models.exam import Exam, ExamResult, ExamStatus


class ExamService:

    @staticmethod
    def _exams_col():
        return get_firestore_client().collection("exams")

    @staticmethod
    def _results_col(exam_id: str):
        return get_firestore_client().collection("exams").document(exam_id).collection("results")

    @classmethod
    def create_exam(
        cls,
        school_id: str,
        class_id: str,
        teacher_id: str,
        exam_name: str,
        subject: str,
        exam_date: str,
        max_marks: float,
    ) -> Exam:
        exam_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc)
        exam = Exam(
            id=exam_id,
            school_id=school_id,
            class_id=class_id,
            teacher_id=teacher_id,
            exam_name=exam_name,
            subject=subject,
            exam_date=exam_date,
            max_marks=max_marks,
            status=ExamStatus.UPCOMING,
            created_at=now,
            updated_at=now,
        )
        cls._exams_col().document(exam_id).set(exam.to_firestore())
        return exam

    @classmethod
    def get_exam(cls, exam_id: str) -> Optional[Exam]:
        doc = cls._exams_col().document(exam_id).get()
        if not doc.exists:
            return None
        return Exam.from_firestore(doc.id, doc.to_dict())

    @classmethod
    def list_class_exams(cls, class_id: str) -> List[Exam]:
        docs = (
            cls._exams_col()
            .where("class_id", "==", class_id)
            .order_by("exam_date")
            .stream()
        )
        return [Exam.from_firestore(d.id, d.to_dict()) for d in docs]

    @classmethod
    def list_school_exams(cls, school_id: str) -> List[Exam]:
        docs = (
            cls._exams_col()
            .where("school_id", "==", school_id)
            .order_by("exam_date")
            .stream()
        )
        return [Exam.from_firestore(d.id, d.to_dict()) for d in docs]

    @classmethod
    def record_result(
        cls,
        exam_id: str,
        school_id: str,
        class_id: str,
        student_id: str,
        obtained_marks: float,
        max_marks: float,
    ) -> ExamResult:
        result_id = ExamResult.make_id(exam_id, student_id)
        now = datetime.now(tz=timezone.utc)
        result = ExamResult(
            id=result_id,
            exam_id=exam_id,
            school_id=school_id,
            class_id=class_id,
            student_id=student_id,
            obtained_marks=obtained_marks,
            max_marks=max_marks,
            created_at=now,
            updated_at=now,
        )
        cls._results_col(exam_id).document(result_id).set(result.to_firestore())
        return result

    @classmethod
    def get_result(cls, exam_id: str, student_id: str) -> Optional[ExamResult]:
        result_id = ExamResult.make_id(exam_id, student_id)
        doc = cls._results_col(exam_id).document(result_id).get()
        if not doc.exists:
            return None
        return ExamResult.from_firestore(doc.id, doc.to_dict())

    @classmethod
    def list_exam_results(cls, exam_id: str) -> List[ExamResult]:
        docs = cls._results_col(exam_id).stream()
        return [ExamResult.from_firestore(d.id, d.to_dict()) for d in docs]

    @classmethod
    def list_student_results(cls, student_id: str, school_id: str) -> List[ExamResult]:
        """Get all exam results for a student across all exams in a school."""
        # Query all exams in the school, then get per-exam result for this student
        exams = cls.list_school_exams(school_id)
        results = []
        for exam in exams:
            r = cls.get_result(exam.id, student_id)
            if r:
                results.append(r)
        return results
