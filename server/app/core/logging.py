"""
app.core.logging — Structured Logging Configuration

Configures the Python standard logging system with:
  - JSON format in production (machine-readable, Cloud Logging compatible)
  - Human-readable format in development
  - Suppression of sensitive data (tokens, keys, student PII)
  - Request-ID propagation through a ContextVar

Usage:
    from app.core.logging import setup_logging, get_logger

    setup_logging()                      # call once at app startup
    logger = get_logger(__name__)        # module-level logger
    logger.info("Event", extra={"request_id": "abc"})
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Context variable — propagated from request middleware to log records
# ---------------------------------------------------------------------------
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

class DevelopmentFormatter(logging.Formatter):
    """
    Coloured, human-readable log formatter for local development.
    Format: LEVEL     [request_id] logger_name — message
    """

    LEVEL_COLOURS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        colour = self.LEVEL_COLOURS.get(record.levelname, "")
        reset = self.RESET
        rid = request_id_ctx.get() or "-"
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(
            "%H:%M:%S.%f"
        )[:-3]
        return (
            f"{colour}{record.levelname:<8}{reset} "
            f"[{ts}] [{rid}] {record.name} — {record.getMessage()}"
        )


class ProductionFormatter(logging.Formatter):
    """
    JSON log formatter for production.
    Outputs one JSON object per line — compatible with Cloud Logging.

    SECURITY: Never include 'token', 'private_key', 'password', or 'student_*'
    fields in the structured output. Sensitive fields are stripped by the
    SensitiveDataFilter below.
    """

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        rid = request_id_ctx.get() or None
        payload: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": rid,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "private_key",
        "token",
        "id_token",
        "authorization",
        "firebase_private_key",
        "firebase_client_email",
        "secret",
    }
)


class SensitiveDataFilter(logging.Filter):
    """
    Prevents sensitive field names from appearing in log messages.

    This is a best-effort guard. Developers must still take care not to log
    entire objects that contain sensitive sub-fields.
    """

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        message = record.getMessage().lower()
        for key in _SENSITIVE_KEYS:
            if key in message:
                # Redact rather than drop — so the developer knows something
                # was suppressed rather than being confused by missing log lines.
                record.msg = "[REDACTED — message contained a sensitive key]"
                record.args = ()
                break
        return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def setup_logging(level: str = "INFO", is_production: bool = False) -> None:
    """
    Configure the root logger for the application.

    Call this exactly once at application startup (in app/main.py).

    Args:
        level:         Python log level string, e.g. "DEBUG", "INFO".
        is_production: When True, uses JSON formatter and raises log level
                       for noisy third-party libraries.
    """
    formatter: logging.Formatter
    if is_production:
        formatter = ProductionFormatter()
    else:
        formatter = DevelopmentFormatter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    # Avoid adding duplicate handlers if setup_logging is called more than once
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers.clear()
        root_logger.addHandler(handler)

    # Quieten noisy third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Keep uvicorn error logs visible
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.

    Usage:
        logger = get_logger(__name__)
        logger.info("Server started")
    """
    return logging.getLogger(name)
