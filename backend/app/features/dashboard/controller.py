"""Dashboard data API."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.domain.entities.user import User
from app.features.auth.dependencies import get_current_active_user, require_officer_or_admin, validate_csrf_token
from app.features.dashboard.dependencies import get_dashboard_service
from app.features.dashboard.schemas import DashboardGenerateRequest, DashboardResponse
from app.features.dashboard.service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard_overview(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    _user: Annotated[User, Depends(get_current_active_user)],
    report_ids: list[str] | None = Query(default=None, alias="reportIds"),
    period: str | None = Query(default=None),
) -> DashboardResponse:
    """Load processed reports and return dashboard JSON."""
    return await service.load_overview(report_ids=report_ids, period=period)


@router.post("/generate", response_model=DashboardResponse)
async def generate_dashboard(
    body: DashboardGenerateRequest,
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    _user: Annotated[User, Depends(require_officer_or_admin)],
    _csrf: None = Depends(validate_csrf_token),
) -> DashboardResponse:
    """Build dashboard JSON from supplied processed reports."""
    return service.generate(body)
