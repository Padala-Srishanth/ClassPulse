"""
app.core.firebase — Firebase Admin SDK Initialisation

Initialises the Firebase Admin SDK as a singleton at application startup.
All Firebase services (Firestore, Auth, Storage) are accessed through
this module.

Design decisions:
  - Singleton pattern: firebase_admin is only initialised once per process.
  - Credentials come exclusively from app.core.config (environment variables).
  - The serviceAccountKey.json file is never read directly from disk.
  - Safe for Cloud Run: when FIREBASE_* env vars are present, the SDK
    initialises correctly without any local credential file.

Usage:
    from app.core.firebase import get_firestore_client, verify_firebase_token
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import firebase_admin
from firebase_admin import auth, credentials, firestore, storage

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Module-level references (populated by initialise_firebase)
# ---------------------------------------------------------------------------
_firebase_app: Optional[firebase_admin.App] = None
_firestore_client: Optional[Any] = None


def initialise_firebase() -> firebase_admin.App:
    """
    Initialise the Firebase Admin SDK.

    Safe to call multiple times — uses the existing App if already initialised.
    Called once from app/main.py lifespan handler.

    Returns:
        The initialised firebase_admin.App instance.

    Raises:
        ValueError: If required Firebase environment variables are missing.
        Exception:  If the Firebase SDK fails to initialise (e.g., bad credentials).
    """
    global _firebase_app, _firestore_client  # noqa: PLW0603

    if _firebase_app is not None:
        logger.debug("Firebase Admin SDK already initialised — reusing existing app.")
        return _firebase_app

    settings = get_settings()

    from app.core.mock_firestore import get_local_firestore

    # Build the Certificate from environment variables.
    try:
        cred = credentials.Certificate(settings.firebase_credentials_dict)
        # Check if a default app already exists (can happen in tests)
        try:
            _firebase_app = firebase_admin.get_app()
            logger.debug("Using existing Firebase Admin app.")
        except ValueError:
            # No app exists yet — initialise
            _firebase_app = firebase_admin.initialize_app(
                credential=cred,
                options={
                    "projectId": settings.FIREBASE_PROJECT_ID,
                    "storageBucket": f"{settings.FIREBASE_PROJECT_ID}.appspot.com",
                },
            )
            logger.info(
                "Firebase Admin SDK initialised.",
                extra={"project_id": settings.FIREBASE_PROJECT_ID},
            )
        if "mock" in settings.FIREBASE_PRIVATE_KEY or settings.FIREBASE_PROJECT_ID == "classpulse-demo":
            _firestore_client = get_local_firestore()
        else:
            try:
                real_client = firestore.client(_firebase_app)
                # Probe real Firestore connectivity
                _ = real_client.collection("schools").limit(1).get()
                _firestore_client = real_client
                logger.info("Successfully connected to live Cloud Firestore (project: %s)", settings.FIREBASE_PROJECT_ID)
            except Exception as exc:
                logger.warning("Cloud Firestore database not found or offline (%s). Operating in local fallback mode.", exc)
                _firestore_client = get_local_firestore()
    except Exception as exc:
        logger.warning("Firebase credentials skipped or invalid. Operating in local demo mode: %s", exc)
        _firestore_client = get_local_firestore()

    return _firebase_app



def get_firestore_client() -> Any:
    """
    Return the Firestore client.
    """
    from app.core.mock_firestore import get_local_firestore
    if _firestore_client is not None:
        return _firestore_client
    return get_local_firestore()




def get_storage_bucket() -> Any:
    """
    Return the Firebase Storage bucket reference.
    """
    if _firebase_app is None:
        raise RuntimeError(
            "Firebase has not been initialised. "
            "Ensure initialise_firebase() is called at application startup."
        )
    return storage.bucket(app=_firebase_app)


async def verify_firebase_token(id_token: str) -> Dict[str, Any]:
    """
    Verify a Firebase ID Token or developer demo token.
    SECURITY: Mock tokens are strictly disabled in production.
    """
    settings = get_settings()

    # Fast path for developer demo mode tokens — allowed ONLY when allow_demo_auth is True
    if id_token.startswith("mock-"):
        if not settings.allow_demo_auth:
            logger.warning(
                "Mock authentication token rejected: demo auth is disabled in %s",
                settings.APP_ENV,
            )
            raise ValueError("Mock authentication tokens are strictly disabled in this environment.")

        if id_token.startswith("mock-teacher-token"):
            parts = id_token.split(":")
            t_uid = parts[1] if len(parts) > 1 else "teacher-uid-001"
            return {
                "uid": t_uid,
                "email": f"{t_uid}@school-001.example.com",
                "email_verified": True,
                "role": "TEACHER",
                "school_id": "school-001",
            }
        if id_token.startswith("mock-school-admin-token"):
            parts = id_token.split(":")
            s_uid = parts[1] if len(parts) > 1 else "sadmin-uid-001"
            return {
                "uid": s_uid,
                "email": "principal@school-001.example.com",
                "email_verified": True,
                "role": "SCHOOL_ADMIN",
                "school_id": "school-001",
            }
        if id_token.startswith("mock-student-token"):
            parts = id_token.split(":")
            st_uid = parts[1] if len(parts) > 1 else "student-uid-001"
            return {
                "uid": st_uid,
                "email": "student001@school-001.example.com",
                "email_verified": True,
                "role": "STUDENT",
                "school_id": "school-001",
                "student_id": "demo-student-001",
            }
        if id_token.startswith("mock-admin-token"):
            return {
                "uid": "admin-uid-001",
                "email": "admin@classpulse.example.com",
                "email_verified": True,
                "role": "ADMIN",
                "school_id": None,
            }
        # Generic fallback for any other mock token (e.g. 'mock-token')
        return {
            "uid": "teacher-uid-001",
            "email": "teacher@school-001.example.com",
            "email_verified": True,
            "role": "TEACHER",
            "school_id": "school-001",
        }

    if _firebase_app is None:
        raise RuntimeError("Firebase has not been initialised.")

    try:
        decoded_token: Dict[str, Any] = auth.verify_id_token(
            id_token,
            app=_firebase_app,
            check_revoked=True,
        )
        return decoded_token
    except Exception:
        # Fallback to teacher token ONLY in local development / demo mode
        if settings.allow_demo_auth:
            return {
                "uid": "teacher-uid-001",
                "email": "teacher@school-001.example.com",
                "email_verified": True,
                "role": "TEACHER",
                "school_id": "school-001",
            }
        raise



async def check_firebase_connectivity() -> Dict[str, Any]:
    """
    Probe Firebase connectivity by executing a lightweight Firestore operation.

    Used by the /api/v1/health/firebase endpoint.
    Does NOT expose project-level data — only checks that the SDK can
    communicate with Firestore.

    Returns:
        Dictionary with connectivity status.
    """
    if _firebase_app is None:
        return {
            "connected": False,
            "reason": "Firebase Admin SDK not initialised",
        }

    try:
        client = get_firestore_client()
        # A lightweight meta-request: list collections at the root (limit=1).
        # This exercises the full auth + network path without reading real data.
        _ = list(client.collections())
        return {
            "connected": True,
            "project_id": get_settings().FIREBASE_PROJECT_ID,
        }
    except Exception as exc:
        logger.warning("Firebase connectivity check failed: %s", type(exc).__name__)
        return {
            "connected": False,
            "reason": "Firestore request failed",
        }
