"""Structured logging with sensitive key sanitization and request correlation."""

import json
import logging
import sys
import time
from contextvars import ContextVar
from typing import Any, Dict, Optional

# Context variable for correlating logs with request IDs
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id_ctx", default=None)

# Sensitive keys that must be scrubbed from structured log payloads
SENSITIVE_KEYS = {
    "password",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "secret_key",
    "authorization",
    "api_key",
    "database_url",
    "cookie",
    "set-cookie",
}


def sanitize_sensitive_data(data: Any) -> Any:
    """Recursively redact sensitive keys in dictionaries and lists."""
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_sensitive_data(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    return data


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get(),
        }

        # Include custom extra fields if provided
        if hasattr(record, "http_method"):
            log_payload["http_method"] = record.http_method
        if hasattr(record, "path"):
            log_payload["path"] = record.path
        if hasattr(record, "status_code"):
            log_payload["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_payload["duration_ms"] = record.duration_ms
        if hasattr(record, "error_code"):
            log_payload["error_code"] = record.error_code

        # Sanitize entire payload before serialization
        sanitized_payload = sanitize_sensitive_data(log_payload)
        return json.dumps(sanitized_payload)


def setup_logging(log_level: str = "INFO", structured: bool = True) -> logging.Logger:
    """Configures application-wide logging."""
    logger = logging.getLogger("dsaapp")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if structured:
        handler.setFormatter(StructuredJsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
            )
        )

    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = setup_logging()
