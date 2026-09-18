"""
app.services.chatbot.scope — Chatbot Authorization & Scope Resolution

This is the single place that decides WHAT data a chatbot request is allowed
to touch. It is evaluated fresh on every request from the Firebase-verified
`CurrentUser` — never from anything the client sends — so a teacher can never
widen their own access by crafting a request, and conversational context from
a previous turn can only narrow a query, never broaden it beyond this scope.

Rules (mirrors the existing `require_school_access` pattern used across the
REST API, extended with class-level scoping for teachers):
  - STUDENT: no chatbot access at all (rejected before this module is reached).
  - TEACHER: authorized classes = classes in their school where
    `class.teacher_ids` contains their uid (the same field principal.py
    already uses to compute per-teacher assignments). Authorized students =
    students enrolled in those classes.
  - SCHOOL_ADMIN / ADMIN ("principal"): authorized classes = every class in
    their school. ADMIN users with no school_id fall back to "school-001",
    matching the existing behaviour in app/api/v1/principal.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Set

from app.core.security import CurrentUser, UserRole
from app.models.class_ import Class
from app.models.student import Student
from app.services.class_service import ClassService
from app.services.student_service import StudentService

# Matches the ADMIN fallback already used in app/api/v1/principal.py so an
# ADMIN account with no school assigned still resolves to a sensible default
# for the demo/single-tenant deployment.
DEFAULT_SCHOOL_ID = "school-001"


class ChatbotAuthorizationError(Exception):
    """Raised when a chatbot request would require data outside the caller's
    authorized scope. Callers should present `str(exc)` to the user verbatim
    — it is always a safe, non-leaking message."""


class ChatbotDataError(Exception):
    """Raised when requested data (a student, class, etc.) cannot be found."""


@dataclass
class ChatScope:
    user: CurrentUser
    school_id: str
    is_principal: bool
    classes: List[Class]
    _students_cache: Optional[List[Student]] = field(default=None, repr=False)

    @property
    def class_ids(self) -> Set[str]:
        return {c.id for c in self.classes}

    def class_by_id(self, class_id: str) -> Optional[Class]:
        return next((c for c in self.classes if c.id == class_id), None)

    def classes_matching(self, grade: Optional[str] = None, section: Optional[str] = None) -> List[Class]:
        result = self.classes
        if grade:
            result = [c for c in result if c.grade.strip().lower() == grade.strip().lower()]
        if section:
            result = [c for c in result if c.section.strip().lower() == section.strip().lower()]
        return result

    def students(self) -> List[Student]:
        """All students within this scope's authorized classes (cached per-request)."""
        if self._students_cache is None:
            students: List[Student] = []
            for c in self.classes:
                students.extend(StudentService.list_class_students(c.id, limit=1000))
            self._students_cache = students
        return self._students_cache

    def is_class_authorized(self, class_id: str) -> bool:
        return class_id in self.class_ids

    def is_student_authorized(self, student: Student) -> bool:
        return student.school_id == self.school_id and student.class_id in self.class_ids

    def require_class(self, class_id: str) -> Class:
        cls = self.class_by_id(class_id)
        if cls is None:
            raise ChatbotAuthorizationError(
                "I can only provide information for the classes you are authorized to access."
            )
        return cls

    def require_student(self, student: Optional[Student]) -> Student:
        if student is None or not self.is_student_authorized(student):
            raise ChatbotAuthorizationError(
                "I couldn't find that student among the students you are authorized to access."
            )
        return student

    def scope_label(self) -> str:
        """Short human-readable description of this scope, for response text."""
        if self.is_principal:
            return "your school"
        return "your classes"


def resolve_scope(user: CurrentUser) -> ChatScope:
    """Resolve the authorized data scope for a chatbot request.

    Raises ChatbotAuthorizationError if the user's role has no chatbot access
    or their account is not linked to a school.
    """
    if user.role not in (UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.ADMIN):
        raise ChatbotAuthorizationError(
            "The ClassPulse Assistant is available to teachers and principals only."
        )

    is_principal = user.role in (UserRole.SCHOOL_ADMIN, UserRole.ADMIN)
    school_id = user.school_id or (DEFAULT_SCHOOL_ID if user.role == UserRole.ADMIN else None)
    if not school_id:
        raise ChatbotAuthorizationError(
            "Your account is not linked to a school yet, so I can't retrieve any ClassPulse data."
        )

    all_classes = ClassService.list_school_classes(school_id, limit=1000)

    if is_principal:
        classes = all_classes
    else:
        classes = [c for c in all_classes if user.uid in (c.teacher_ids or [])]

    return ChatScope(user=user, school_id=school_id, is_principal=is_principal, classes=classes)
