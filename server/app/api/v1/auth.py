"""
app.api.v1.auth — Role-Based Authentication Endpoint

Provides a demo/local authentication endpoint that validates credentials
against the EXISTING Firestore data (students, teachers, principal).

NO new users are created.
NO passwords are stored.
NO schema changes are made.

Credential contract:
  Student:   username = student_code (e.g. "DPS-10A-01"), password = student_code
  Teacher:   username = teacher firebase_uid (e.g. "teacher-uid-001"), password = same uid
  Principal: username = "sadmin-uid-001", password = "sadmin-uid-001"

On success, returns a mock session token compatible with the existing
verify_firebase_token() in app.core.firebase — so all downstream
API calls work exactly as before with no changes to protected routes.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.utils.responses import error_response, success_response
from app.services.student_service import StudentService
from app.services.user_service import UserService
from app.core.security import UserRole

router = APIRouter(tags=["Auth"])


class LoginRequest(BaseModel):
    role: str          # "STUDENT" | "TEACHER" | "PRINCIPAL"
    username: str      # student_code / teacher uid / principal uid
    password: str      # same as username (credential = identifier)


@router.post("/login", summary="Validate credentials against existing data and return a session token")
async def demo_login(payload: LoginRequest):
    """
    Validates the provided credentials against the existing Firestore data.
    Does NOT create any new records or modify existing data.

    Returns a mock session token on success which is compatible with the
    existing token verification mechanism in app.core.firebase.
    """
    role = payload.role.upper()
    username = payload.username.strip()
    password = payload.password.strip()

    # Basic validation: password must equal username (identifier = credential)
    if username != password:
        return error_response(
            code="AUTH_INVALID_CREDENTIALS",
            message="Invalid credentials. Please check your username and password.",
            status_code=401,
        )

    if not username:
        return error_response(
            code="AUTH_MISSING_CREDENTIALS",
            message="Username and password are required.",
            status_code=400,
        )

    # -----------------------------------------------------------------------
    # STUDENT LOGIN
    # Validate that the student_code exists in the existing students collection
    # -----------------------------------------------------------------------
    if role == "STUDENT":
        # Query all schools for this student code; for this demo, use school-001
        student = StudentService.get_student_by_code("school-001", username)
        if not student:
            # Also try searching all classes directly since student_code might vary
            return error_response(
                code="AUTH_INVALID_CREDENTIALS",
                message="Student code not found. Please check your roll number.",
                status_code=401,
            )

        # Return a session token that the existing frontend + backend understand
        return success_response(data={
            "token": f"mock-student-token:{student.id}",
            "user": {
                "id": student.id,
                "firebase_uid": student.id,
                "email": f"{username}@school-001.example.com",
                "name": student.name,
                "role": "STUDENT",
                "school_id": student.school_id,
                "status": "ACTIVE",
                "student_id": student.id,
                "class_id": student.class_id,
                "student_code": student.student_code,
            },
        })

    # -----------------------------------------------------------------------
    # TEACHER LOGIN
    # Validate that the teacher uid exists in the existing users collection
    # -----------------------------------------------------------------------
    elif role == "TEACHER":
        user = UserService.get_user(username)
        if not user or user.role != UserRole.TEACHER:
            return error_response(
                code="AUTH_INVALID_CREDENTIALS",
                message="Teacher ID not found. Please check your credentials.",
                status_code=401,
            )

        return success_response(data={
            "token": f"mock-teacher-token:{user.id}",
            "user": {
                "id": user.id,
                "firebase_uid": user.firebase_uid,
                "email": user.email,
                "name": user.name,
                "role": "TEACHER",
                "school_id": user.school_id,
                "status": "ACTIVE",
            },
        })

    # -----------------------------------------------------------------------
    # PRINCIPAL LOGIN
    # Validate that the principal uid exists in the existing users collection
    # -----------------------------------------------------------------------
    elif role in ("PRINCIPAL", "SCHOOL_ADMIN"):
        user = UserService.get_user(username)
        if not user or user.role not in (UserRole.SCHOOL_ADMIN, UserRole.ADMIN):
            return error_response(
                code="AUTH_INVALID_CREDENTIALS",
                message="Principal ID not found. Please check your credentials.",
                status_code=401,
            )

        return success_response(data={
            "token": f"mock-school-admin-token:{user.id}",
            "user": {
                "id": user.id,
                "firebase_uid": user.firebase_uid,
                "email": user.email,
                "name": user.name,
                "role": "SCHOOL_ADMIN",
                "school_id": user.school_id,
                "status": "ACTIVE",
            },
        })

    else:
        return error_response(
            code="AUTH_INVALID_ROLE",
            message=f"Unknown role: {role}. Must be STUDENT, TEACHER, or PRINCIPAL.",
            status_code=400,
        )
