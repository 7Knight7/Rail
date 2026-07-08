"""Shared automation utilities."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Keys reserved on logging.LogRecord — must not appear in logger.info(..., extra={...}).
_RESERVED_LOGRECORD_KEYS = frozenset(
    {
        "name",
        "msg",
        "args",
        "created",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "thread",
        "threadName",
        "exc_info",
        "exc_text",
        "stack_info",
        "taskName",
    }
)

# Preferred safe aliases for common automation structured fields.
_LOG_FIELD_ALIASES = {
    "name": "field_name",
    "type": "field_type",
    "label": "field_label",
    "value": "field_value",
    "id": "field_id",
}


def _sanitize_log_extra(fields: dict[str, object]) -> dict[str, object]:
    """Rename keys that collide with LogRecord reserved attributes."""
    sanitized: dict[str, object] = {}
    for key, value in fields.items():
        if key in _LOG_FIELD_ALIASES:
            sanitized[_LOG_FIELD_ALIASES[key]] = value
        elif key in _RESERVED_LOGRECORD_KEYS:
            sanitized[f"log_{key}"] = value
        else:
            sanitized[key] = value
    return sanitized


def ensure_directory(path: Path) -> Path:
    """Create a directory if it does not exist and return the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_url(url: str) -> str:
    """Normalize a URL for comparison (lowercase host, no trailing slash)."""
    return url.rstrip("/").lower()


def log_automation_event(logger: logging.Logger, event: str, **fields: object) -> None:
    """Emit a structured automation log line with consistent extra fields."""
    safe_fields = _sanitize_log_extra(fields)
    parts = [f"{key}={value}" for key, value in safe_fields.items()]
    message = event if not parts else f"{event} | {' | '.join(parts)}"
    logger.info(message, extra={"automation_event": event, **safe_fields})
