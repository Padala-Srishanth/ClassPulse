"""
app.main — FastAPI Application Factory

This module creates and configures the FastAPI application instance.

Responsibilities:
  - Create the FastAPI app with metadata (title, version, docs URLs)
  - Register global middleware (CORS, request logging)
  - Register global exception handlers
  - Mount the API router
  - Manage the application lifespan (startup / shutdown events)

Architecture note:
  - This module is intentionally thin — it wires components together.
  - Business logic lives in services/; HTTP logic lives in api/v1/; core
    infrastructure lives in core/. main.py only assembles them.

Entry points:
  - Local development: python run.py
  - Production:        uvicorn app.main:app --host 0.0.0.0 --port 8000
  - Docker / Cloud Run: the Dockerfile CMD points to this module
"""

from __future__ import annotations

import traceback
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.firebase import initialise_firebase
from app.core.logging import get_logger, setup_logging
from app.middleware.request_logging import RequestLoggingMiddleware

# ---------------------------------------------------------------------------
# Bootstrap logging before anything else so startup messages are captured.
# ---------------------------------------------------------------------------
settings = get_settings()

setup_logging(
    level=settings.LOG_LEVEL,
    is_production=settings.is_production,
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — startup and shutdown hooks
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Startup:
      - Initialise Firebase Admin SDK
      - Log readiness

    Shutdown:
      - Log graceful shutdown (Firebase Admin has no explicit cleanup needed)

    This replaces the deprecated @app.on_event("startup") pattern.
    """
    # === STARTUP ===
    logger.info("ClassPulse API starting up. env=%s version=%s", settings.APP_ENV, settings.APP_VERSION)

    try:
        initialise_firebase()
        logger.info("Firebase Admin SDK initialised successfully.")
    except Exception:
        logger.error(
            "CRITICAL: Firebase Admin SDK failed to initialise. "
            "Check FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, and FIREBASE_PRIVATE_KEY "
            "environment variables. The server will start but Firebase-dependent "
            "endpoints will not function."
        )
        # We intentionally do NOT raise here — we want the server to start so
        # the /health endpoint can still respond (useful for debugging in cloud).

    logger.info("ClassPulse API is ready. Listening on %s:%d", settings.HOST, settings.PORT)

    yield  # Application runs here

    # === SHUTDOWN ===
    logger.info("ClassPulse API shutting down gracefully.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns a fully configured FastAPI instance. Separated into a factory
    function so tests can create isolated app instances.
    """
    _settings = get_settings()

    app = FastAPI(
        title=_settings.APP_NAME,
        version=_settings.APP_VERSION,
        description=(
            "**ClassPulse API** — AI-driven early learning-gap detection system.\n\n"
            "Identifies students showing signs of academic decline weeks before "
            "conventional exams reveal the problem, giving teachers actionable, "
            "explainable early warnings.\n\n"
            "### Authentication\n"
            "Protected endpoints require a **Firebase ID Token** in the "
            "`Authorization: Bearer <token>` header.\n\n"
            "### Versioning\n"
            "All endpoints are versioned under `/api/v1/`. Breaking changes "
            "will be introduced under `/api/v2/`."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        # Disable the default 422 handler so we can use our standard envelope
        # (see RequestValidationError handler below).
    )

    # -------------------------------------------------------------------------
    # Middleware — ORDER MATTERS: added last = executed first for requests
    # -------------------------------------------------------------------------

    # 1. CORS — must be the outermost middleware so preflight OPTIONS requests
    #    are handled before any auth or business logic runs.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    # 2. Request logging — generates request_id, logs timing and status.
    app.add_middleware(RequestLoggingMiddleware)

    # -------------------------------------------------------------------------
    # Exception handlers
    # -------------------------------------------------------------------------

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handle Pydantic validation errors (422 Unprocessable Entity).

        Returns a consistent error envelope instead of FastAPI's default format.
        In development, includes the validation details.
        In production, hides details to prevent schema enumeration.
        """
        logger.warning("Request validation failed. path=%s", request.url.path)

        details = None
        if not _settings.HIDE_ERROR_DETAILS:
            # Safe to include in dev — these are schema validation messages, not
            # internal paths or secrets.
            details = exc.errors()

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request body or parameters failed validation.",
                    "details": details,
                },
                "meta": {"request_id": None, "timestamp": None},
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Catch-all handler for unhandled exceptions.

        SECURITY:
          - In production: returns a generic error message with no internal details.
          - In development: includes the exception type and traceback.
          - Stack traces and internal paths are NEVER included in production.

        All unhandled exceptions are logged at ERROR level so they appear
        in Cloud Logging and trigger monitoring alerts.
        """
        logger.error(
            "Unhandled exception. path=%s method=%s error=%s",
            request.url.path,
            request.method,
            type(exc).__name__,
            exc_info=True,
        )

        details = None
        if not _settings.HIDE_ERROR_DETAILS and not _settings.is_production:
            details = {
                "type": type(exc).__name__,
                "traceback": traceback.format_exc(),
            }

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": (
                        "An unexpected error occurred. "
                        "Please try again or contact support if the problem persists."
                    ),
                    "details": details,
                },
                "meta": {"request_id": None, "timestamp": None},
            },
        )

    # -------------------------------------------------------------------------
    # Routers
    # -------------------------------------------------------------------------
    app.include_router(api_router)

    # -------------------------------------------------------------------------
    # Root redirect (helpful for developers hitting the bare domain)
    # -------------------------------------------------------------------------
    @app.get("/", include_in_schema=False)
    async def root():
        return JSONResponse(
            content={
                "message": f"Welcome to {_settings.APP_NAME} v{_settings.APP_VERSION}",
                "docs": "/docs",
                "health": "/api/v1/health",
            }
        )

    return app


# ---------------------------------------------------------------------------
# Module-level app instance (used by uvicorn and run.py)
# ---------------------------------------------------------------------------
app = create_application()
