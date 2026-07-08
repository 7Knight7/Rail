"""Shared automation utilities."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def ensure_directory(path: Path) -> Path:
    """Create a directory if it does not exist and return the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_url(url: str) -> str:
    """Normalize a URL for comparison (lowercase host, no trailing slash)."""
    return url.rstrip("/").lower()
