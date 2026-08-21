"""
app.core.security — Authentication & Authorisation Foundation

Provides the reusable FastAPI dependency `get_current_user` that:
  1. Extracts the Bearer token from the Authorization header
  2. Verifies it with Firebase Admin SDK
  3. Returns a typed CurrentUser model

This dependency will be injected into all protected routes in Phase 2+.
Phase 1 only defines it — no routes require authentication yet.

Role model (enforced via Firebase Custom Claims):
    ADMIN        — ClassPulse platform administrators
    SCHOOL_ADMIN — Administrators of one or more schools
    TEACHER      — Classroom teachers with class-scoped access

RECOMMENDATION implemented:
    Roles and school_id are stored as Firebase Custom Claims, not in Firestore.
    This eliminates a Firestore read on every authenticated request.

Usage (in any future protected route):
    from app.core.security import get_current_user, CurrentUser, require_role

    @router.get("/students")
    async def list_students(user: CurrentUser = Depends(get_current_user)):
        ...
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.firebase import verify_firebase_token
from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# HTTP Bearer scheme — FastAPI extracts and validates the Authorization header
# ---------------------------------------------------------------------------
_bearer_scheme = HTTPBearer(
    scheme_name="Firebase ID Token",
    description="Firebase Authentication ID Token obtained after signing in.",
    auto_error=True,  # Raises 403 automatically if header is missing
)


# ---------------------------------------------------------------------------
# Role Model
# ---------------------------------------------------------------------------

class UserRole(str, Enum):
    """
    Application-level roles stored as Firebase Custom Claims.

    To assign a role to a user:
        firebase_admin.auth.set_custom_user_claims(uid, {"role": "TEACHER", "school_id": "..."})

    The role is then available in every verified ID token without additional
    database lookups.
    """

    ADMIN = "ADMIN"
    SCHOOL_ADMIN = "SCHOOL_ADMIN"
    TEACHER = "TEACHER"


# ---------------------------------------------------------------------------
# CurrentUser — typed representation of a verified Firebase identity
# ---------------------------------------------------------------------------

class CurrentUser(BaseModel):
    """
    Represents an authenticated and verified API caller.

    Populated from the decoded Firebase ID Token after successful verification.
    Injected into route handlers via the get_current_user dependency.

    Attributes:
        uid:        Firebase UID (unique, stable identifier for the user).
        email:      User's email address (may be None if not set).
        role:       Application role from Custom Claims. None means no role assigned yet.
        school_id:  The school this user belongs to (from Custom Claims).
                    ADMIN users may have this as None (access to all schools).
    """

    uid: str
    email: Optional[str] = None
    email_verified: bool = False
    role: Optional[UserRole] = None
    school_id: Optional[str] = None

    @property
    def is_admin(self) -> bool:
        """True if the user has platform-level admin access."""
        return self.role == UserRole.ADMIN

    @property
    def is_school_admin(self) -> bool:
        """True if the user is a school administrator."""
        return self.role in {UserRole.ADMIN, UserRole.SCHOOL_ADMIN}

    @property
    def is_teacher(self) -> bool:
        """True if the user has teacher-level access (or higher)."""
        return self.role in {UserRole.ADMIN, UserRole.SCHOOL_ADMIN, UserRole.TEACHER}

    @property
    def has_school(self) -> bool:
        """True if this user is associated with a specific school."""
        return self.school_id is not None


# ---------------------------------------------------------------------------
# FastAPI Dependency
# ---------------------------------------------------------------------------

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> CurrentUser:
    """
    FastAPI dependency that verifies a Firebase ID Token and returns the caller.

    Inject this into any route that requires authentication:
        user: CurrentUser = Depends(get_current_user)

    Raises:
        HTTPException 401: Token is missing, malformed, expired, or revoked.
        HTTPException 401: The user's account is disabled.
        HTTPException 500: Unexpected error during token verification.
    """
    token = credentials.credentials

    try:
        decoded = await verify_firebase_token(token)
    except Exception as exc:
        exc_name = type(exc).__name__
        logger.warning(
            "Token verification failed. error_type=%s uid=<unknown>",
            exc_name,
        )

        # Map Firebase exception names to user-facing messages.
        # SECURITY: Do not expose the raw exception message — it may contain
        # internal details. Only the exception type is safe to map.
        _firebase_error_map = {
            "InvalidIdTokenError": "The provided token is invalid.",
            "ExpiredIdTokenError": "The provided token has expired. Please sign in again.",
            "RevokedIdTokenError": "The provided token has been revoked. Please sign in again.",
            "UserDisabledError": "This user account has been disabled.",
            "CertificateFetchError": "Unable to verify token at this time. Please try again.",
        }
        message = _firebase_error_map.get(exc_name, "Authentication failed.")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_TOKEN_INVALID", "message": message},
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Build the CurrentUser from the decoded token.
    # Custom Claims (role, school_id) are set by backend admin endpoints.
    uid = decoded.get("uid") or decoded.get("sub", "")
    user = CurrentUser(
        uid=uid,
        email=decoded.get("email"),
        email_verified=decoded.get("email_verified", False),
        role=decoded.get("role"),      # Custom Claim — may be None until provisioned
        school_id=decoded.get("school_id"),  # Custom Claim
    )

    logger.debug("Authenticated request. uid=%s role=%s", user.uid, user.role)
    return user


# ---------------------------------------------------------------------------
# Role-enforcement helpers (used in Phase 2+ route guards)
# ---------------------------------------------------------------------------

def require_role(*roles: UserRole):
    """
    Factory that returns a FastAPI dependency enforcing one of the given roles.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            user: CurrentUser = Depends(require_role(UserRole.ADMIN))
        ):
            ...
    """
    async def _dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            logger.warning(
                "Authorisation denied. uid=%s role=%s required_roles=%s",
                user.uid,
                user.role,
                [r.value for r in roles],
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "AUTH_INSUFFICIENT_ROLE",
                    "message": "You do not have permission to perform this action.",
                },
            )
        return user

    return _dependency


def require_school_access(school_id: str, user: CurrentUser) -> None:
    """
    Verify that the current user has access to the given school.

    ADMIN users bypass this check (they have access to all schools).
    SCHOOL_ADMIN and TEACHER users must belong to the specified school.

    Args:
        school_id: The school ID being accessed.
        user:      The verified CurrentUser.

    Raises:
        HTTPException 403: The user does not belong to this school.
    """
    if user.is_admin:
        return  # ADMINs have access to all schools

    if user.school_id != school_id:
        logger.warning(
            "Cross-school access attempt. uid=%s user_school=%s requested_school=%s",
            user.uid,
            user.school_id,
            school_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "AUTH_SCHOOL_ACCESS_DENIED",
                "message": "You do not have access to this school's data.",
            },
        )
