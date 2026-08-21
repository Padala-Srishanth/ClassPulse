"""
app.api.v1.health — Health Check Endpoints

Provides two public endpoints that require no authentication:

    GET /api/v1/health
        Liveness probe — confirms the FastAPI process is running.
        Used by Cloud Run / load balancers.

    GET /api/v1/health/firebase
        Readiness probe — confirms Firebase connectivity.
        Does NOT expose credentials or internal project data.

These endpoints are intentionally public (no auth required) because they
need to be callable by infrastructure health checks before authentication
is available.

SECURITY:
    - Firebase connectivity response does NOT expose connection strings,
      private keys, or sensitive project data.
    - Only the project_id is included (it is already in the frontend config).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.firebase import check_firebase_connectivity
from app.core.logging import get_logger
from app.utils.responses import success_response

logger = get_logger(__name__)
router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get(
    "/health",
    summary="Liveness Check",
    description=(
        "Returns OK if the ClassPulse API process is running. "
        "Used by load balancers and container orchestrators as a liveness probe. "
        "Does not check external dependencies."
    ),
    response_description="Service liveness status.",
)
async def health_check():
    """
    Liveness probe.

    Always returns 200 if the process is alive and the request reached FastAPI.
    Does NOT check Firebase, database, or any external dependency.

    Use `/health/firebase` for a full readiness probe.
    """
    logger.debug("Liveness probe called.")
    return success_response(
        data={
            "status": "ok",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
    )


@router.get(
    "/health/firebase",
    summary="Firebase Connectivity Check",
    description=(
        "Verifies that the ClassPulse API can reach Firebase services. "
        "Returns connected=true if Firestore is reachable. "
        "Returns connected=false with a reason if connectivity fails. "
        "Does NOT expose credentials or internal Firebase details."
    ),
    response_description="Firebase connectivity status.",
)
async def health_firebase():
    """
    Firebase readiness probe.

    Executes a lightweight, read-only Firestore operation to confirm connectivity.
    The operation does not read any application data — only confirms that the
    Firebase Admin SDK can authenticate and reach Firestore.

    Status codes:
        200 — Firebase responded (connected or not — inspect `data.connected`)
        200 — always returned; check `data.connected` for the actual result.

    Note: A 200 with connected=false means the API is running but Firebase
    is unreachable. The calling infrastructure should treat this as degraded.
    """
    logger.debug("Firebase connectivity probe called.")
    connectivity = await check_firebase_connectivity()

    return success_response(
        data={
            "service": "firebase",
            "connected": connectivity.get("connected", False),
            "project_id": connectivity.get("project_id"),
            "reason": connectivity.get("reason"),
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
    )
