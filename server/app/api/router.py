"""
app.api.router — Top-Level API Router

Mounts all versioned sub-routers under the /api prefix.

Versioning strategy:
    /api/v1/...  — Current stable API
    /api/v2/...  — Future breaking changes (added here when needed)

To add a new v1 route module:
    1. Create app/api/v1/your_module.py
    2. Import its router here
    3. Add: v1_router.include_router(your_module.router, prefix="/your-prefix")

Phase 2 will add:
    v1_router.include_router(schools.router, prefix="/schools")
    v1_router.include_router(students.router, prefix="/students")
    v1_router.include_router(ingestion.router, prefix="/ingestion")
"""

from fastapi import APIRouter

from app.api.v1 import (
    classes,
    health,
    ingestion,
    interventions,
    risk,
    schools,
    students,
    users,
)

# ---------------------------------------------------------------------------
# V1 router — all current routes live under /api/v1
# ---------------------------------------------------------------------------
v1_router = APIRouter(prefix="/v1")

v1_router.include_router(health.router)
v1_router.include_router(schools.router, prefix="/schools")
v1_router.include_router(users.router, prefix="/users")
v1_router.include_router(classes.router, prefix="/classes")
v1_router.include_router(students.router, prefix="/students")
v1_router.include_router(ingestion.router, prefix="/ingestion")
v1_router.include_router(risk.router, prefix="/risk")
v1_router.include_router(interventions.router, prefix="/interventions")


# ---------------------------------------------------------------------------
# Top-level API router — mounted at /api in main.py
# ---------------------------------------------------------------------------
api_router = APIRouter(prefix="/api")
api_router.include_router(v1_router)


