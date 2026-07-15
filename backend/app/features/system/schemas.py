"""Pydantic schemas for the system info API."""

from pydantic import BaseModel


class SystemComponentStatus(BaseModel):
    ok: bool
    detail: str | None = None


class SystemInfoResponse(BaseModel):
    app_version: str
    environment: str
    backend: SystemComponentStatus
    database: SystemComponentStatus
    database_type: str
    cdp: SystemComponentStatus
    automation_status: str
    active_run_id: str | None = None
    last_successful_run_at: str | None = None
    last_failed_run_at: str | None = None
    storage_usage_bytes: int


class ClearCacheResponse(BaseModel):
    success: bool = True
    cleared: list[str]
