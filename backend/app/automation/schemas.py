"""Pydantic schemas for in-process automation API responses."""

from typing import Any

from pydantic import BaseModel, Field


class AutomationStartResult(BaseModel):
    """Outcome of a CDP attach, navigation, filter, and generation attempt."""

    success: bool
    connected: bool
    tab_found: bool
    url: str | None = None
    title: str | None = None
    error: str | None = None
    report_reached: bool = False
    report_name: str | None = None
    screenshot_path: str | None = None
    report_generated: bool = False
    filters_applied: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int | None = None
    screenshot_before_path: str | None = None
    screenshot_after_path: str | None = None
