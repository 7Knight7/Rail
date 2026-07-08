"""API routes for in-process browser automation."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.automation.dependencies import get_automation_service
from app.automation.schemas import AutomationStartResult
from app.automation.service import AutomationService
from app.domain.entities.user import User
from app.features.auth.dependencies import require_admin, validate_csrf_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/automation", tags=["automation"])


@router.post(
    "/start",
    response_model=AutomationStartResult,
    dependencies=[Depends(require_admin), Depends(validate_csrf_token)],
)
async def start_automation(
    service: Annotated[AutomationService, Depends(get_automation_service)],
    _user: Annotated[User, Depends(require_admin)],
) -> AutomationStartResult:
    """Connect to Chrome via CDP and activate the RailMadad tab."""
    try:
        result = await service.start()
    except Exception as exc:
        logger.exception("Unexpected automation start failure")
        raise HTTPException(status_code=500, detail="Automation failed to start") from exc

    logger.info(
        "Automation start completed: success=%s connected=%s tab_found=%s url=%s",
        result.success,
        result.connected,
        result.tab_found,
        result.url,
    )
    return result
