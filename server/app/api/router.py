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
    announcements,
    assignments,
    classes,
    doubts,
    exams,
    health,
    ingestion,
    interventions,
    intervention_recommendations,
    monthly_reports,
    principal,
    risk,
    schools,
    student_portal,
    students,
    timetables,
    uploads,
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
# Phase 5 routes
v1_router.include_router(principal.router, prefix="/principal")
v1_router.include_router(exams.router, prefix="/exams")
v1_router.include_router(timetables.router, prefix="/timetables")
v1_router.include_router(assignments.router, prefix="/assignments")
v1_router.include_router(doubts.router, prefix="/doubts")
v1_router.include_router(announcements.router, prefix="/announcements")
v1_router.include_router(student_portal.router, prefix="/student")
v1_router.include_router(uploads.router, prefix="/uploads")
v1_router.include_router(monthly_reports.router, prefix="/monthly-reports")


# ---------------------------------------------------------------------------
# Top-level API router — mounted at /api in main.py
# ---------------------------------------------------------------------------
api_router = APIRouter(prefix="/api")
api_router.include_router(v1_router)


