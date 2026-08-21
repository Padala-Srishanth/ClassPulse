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

    # Build the Certificate from environment variables.
    # SECURITY: firebase_credentials_dict is never logged.
    try:
        cred = credentials.Certificate(settings.firebase_credentials_dict)
    except Exception as exc:
        logger.error(
            "Failed to build Firebase credentials from environment variables. "
            "Ensure FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, and "
            "FIREBASE_PRIVATE_KEY are set correctly."
        )
        raise

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

    # Pre-warm the Firestore client (avoids first-request latency)
    _firestore_client = firestore.client(_firebase_app)

    return _firebase_app


def get_firestore_client() -> Any:
    """
    Return the Firestore client.

    Raises:
        RuntimeError: If firebase has not been initialised yet.
    """
    if _firestore_client is None:
        raise RuntimeError(
            "Firebase has not been initialised. "
            "Ensure initialise_firebase() is called at application startup."
        )
    return _firestore_client


def get_storage_bucket() -> Any:
    """
    Return the Firebase Storage bucket reference.

    Used in Phase 2+ for CSV/Excel upload handling.

    Raises:
        RuntimeError: If firebase has not been initialised yet.
    """
    if _firebase_app is None:
        raise RuntimeError(
            "Firebase has not been initialised. "
            "Ensure initialise_firebase() is called at application startup."
        )
    return storage.bucket(app=_firebase_app)


async def verify_firebase_token(id_token: str) -> Dict[str, Any]:
    """
    Verify a Firebase ID Token and return the decoded token claims.

    This is a cryptographic verification against Firebase's public keys.
    It does NOT make a network call for every request — only to refresh
    Firebase's public key cache (approximately every hour).

    Args:
        id_token: The raw JWT Bearer token from the Authorization header.

    Returns:
        Decoded token dictionary containing at minimum:
          - uid: str
          - email: str (if set)
          - email_verified: bool
          - role: str (if custom claim is set)
          - school_id: str (if custom claim is set)

    Raises:
        firebase_admin.auth.InvalidIdTokenError: Token is malformed.
        firebase_admin.auth.ExpiredIdTokenError: Token has expired.
        firebase_admin.auth.RevokedIdTokenError: Token has been revoked.
        firebase_admin.auth.UserDisabledError: The user account is disabled.
    """
    if _firebase_app is None:
        raise RuntimeError("Firebase has not been initialised.")

    # firebase_admin.auth.verify_id_token is synchronous.
    # Running it as-is inside an async function is acceptable for light loads;
    # Phase 3 can move this to a thread pool executor if latency becomes an issue.
    decoded_token: Dict[str, Any] = auth.verify_id_token(
        id_token,
        app=_firebase_app,
        check_revoked=True,  # Adds a network call only when token is flagged
    )
    return decoded_token


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
