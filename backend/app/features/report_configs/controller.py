"""Saved report configuration API."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.exceptions import NotFoundError
from app.domain.entities.user import User
from app.features.auth.dependencies import get_current_active_user, require_officer_or_admin, validate_csrf_token
from app.features.report_configs.store import SaveReportConfigRequest, SavedReportConfigResponse, SavedReportConfigStore

router = APIRouter(prefix="/report-configs", tags=["report-configs"])

_store = SavedReportConfigStore()


@router.get("/{report_id}", response_model=SavedReportConfigResponse)
async def get_saved_report_config(
    report_id: str,
    user: Annotated[User, Depends(get_current_active_user)],
) -> SavedReportConfigResponse:
    saved = _store.load(user.id, report_id)
    if not saved:
        raise NotFoundError("Saved report configuration", report_id)
    return saved


@router.put("/{report_id}", response_model=SavedReportConfigResponse)
async def save_report_config(
    report_id: str,
    body: SaveReportConfigRequest,
    user: Annotated[User, Depends(require_officer_or_admin)],
    _csrf: None = Depends(validate_csrf_token),
) -> SavedReportConfigResponse:
    return _store.save(user.id, report_id, body.configuration)
