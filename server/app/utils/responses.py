"""
app.utils.responses — Standardised API Response Helpers

Every API response from ClassPulse uses one of two shapes:

Success:
    {
        "success": true,
        "data": { ... },
        "meta": {
            "request_id": "...",
            "timestamp": "..."
        }
    }

Error:
    {
        "success": false,
        "error": {
            "code": "SOME_ERROR_CODE",
            "message": "Human-readable description.",
            "details": null
        },
        "meta": {
            "request_id": "...",
            "timestamp": "..."
        }
    }

Rules:
  - "code" is always SCREAMING_SNAKE_CASE (used by frontend for i18n).
  - "message" is always human-readable English (for display / logging).
  - "details" is included only in development mode.
  - Stack traces and internal paths are NEVER included in responses.

Usage:
    from app.utils.responses import success_response, error_response

    return success_response(data={"status": "ok"})
    return error_response(code="NOT_FOUND", message="Student not found.", status_code=404)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from app.core.logging import request_id_ctx


def _build_meta() -> Dict[str, Any]:
    """Build the standard metadata block included in every response."""
    return {
        "request_id": request_id_ctx.get(),
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }


def success_response(
    data: Any,
    status_code: int = 200,
) -> JSONResponse:
    """
    Return a standardised success response.

    Args:
        data:        The payload to return under the "data" key.
        status_code: HTTP status code (default 200).

    Returns:
        JSONResponse with the standard success envelope.
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "data": data,
            "meta": _build_meta(),
        },
    )


def error_response(
    code: str,
    message: str,
    status_code: int = 400,
    details: Optional[Any] = None,
) -> JSONResponse:
    """
    Return a standardised error response.

    Args:
        code:        SCREAMING_SNAKE_CASE error code for frontend handling.
        message:     Human-readable error description.
        status_code: HTTP status code (default 400).
        details:     Optional additional detail (only safe in development).
                     Must be sanitised by the caller before passing here.

    Returns:
        JSONResponse with the standard error envelope.
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details,
            },
            "meta": _build_meta(),
        },
    )


# ---------------------------------------------------------------------------
# Pydantic schema for OpenAPI documentation of the error envelope
# ---------------------------------------------------------------------------

from pydantic import BaseModel  # noqa: E402


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    meta: Dict[str, Any]


class SuccessResponse(BaseModel):
    success: bool = True
    data: Any
    meta: Dict[str, Any]
