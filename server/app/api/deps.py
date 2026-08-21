"""
app.api.deps — Shared FastAPI Dependencies

This module contains FastAPI dependency functions that are shared across
multiple routes and API versions.

It acts as the single import point for route handlers that need injected
resources like the authenticated user, the Firestore client, or settings.

Why deps.py is separate from core/security.py:
    - core/ has no FastAPI imports; it only contains pure Python logic.
    - api/deps.py is the HTTP-layer bridge that wires core logic into FastAPI's
      Depends() injection system.
    - Keeps core/ testable without a running FastAPI application.

Phase 2+ will add more dependencies here:
    - get_db()       → Firestore client injection
    - pagination()   → Common pagination query params
    - school_scope() → School-scoped access helper
"""

# Re-export auth dependencies from core so route handlers have a single
# import location for all dependencies.
from app.core.security import (  # noqa: F401
    CurrentUser,
    UserRole,
    get_current_user,
    require_role,
    require_school_access,
)
from app.core.firebase import get_firestore_client  # noqa: F401
from fastapi import Query
from pydantic import BaseModel


class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 50


def get_pagination(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max number of records to return"),
) -> PaginationParams:
    return PaginationParams(skip=skip, limit=limit)

