"""
app.middleware.request_logging — Request / Response Logging Middleware

Responsibilities:
  1. Generate a unique request_id for every inbound HTTP request
  2. Inject it into the logging ContextVar (propagates to all log lines)
  3. Add X-Request-ID to the response headers (aids client-side debugging)
  4. Log: method, path, status code, and response duration
  5. Attach the request_id to every log line via ContextVar

SECURITY:
  - Never logs Authorization headers, tokens, or request body contents.
  - The path is logged but query strings are sanitised for sensitive params.

Usage (registered in app/main.py):
    app.add_middleware(RequestLoggingMiddleware)
"""

import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger, request_id_ctx

logger = get_logger(__name__)

# Query parameter names that should never appear in logs.
_SENSITIVE_QUERY_PARAMS = frozenset({"token", "api_key", "key", "secret", "password"})


def _sanitise_path(request: Request) -> str:
    """
    Build a loggable path string, redacting any sensitive query parameters.
    """
    path = request.url.path
    params = dict(request.query_params)
    sanitised = {
        k: "***" if k.lower() in _SENSITIVE_QUERY_PARAMS else v
        for k, v in params.items()
    }
    if sanitised:
        qs = "&".join(f"{k}={v}" for k, v in sanitised.items())
        return f"{path}?{qs}"
    return path


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that adds request-scoped logging and timing.

    Each request receives a UUID-based request_id that:
      - Is set on the request_id_ctx ContextVar (all log lines pick it up)
      - Is returned in the X-Request-ID response header

    Log format:
        INFO  → {method} {path} completed in {duration}ms status={code}
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate a unique ID for this request
        request_id = str(uuid.uuid4())

        # Set in ContextVar — propagates to all logger calls in this async context
        token = request_id_ctx.set(request_id)

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            # Re-raise; the global exception handler in main.py will catch it.
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            path = _sanitise_path(request)
            status_code = getattr(response, "status_code", 500) if "response" in dir() else 500  # noqa: F821

            log_fn = logger.info if status_code < 400 else logger.warning
            if status_code >= 500:
                log_fn = logger.error

            log_fn(
                "%s %s → %d  (%.1f ms)",
                request.method,
                path,
                status_code,
                elapsed_ms,
            )

            # Restore the ContextVar token
            request_id_ctx.reset(token)

        # Attach the request_id to the response so clients can correlate logs
        response.headers["X-Request-ID"] = request_id
        return response
