"""API routes for in-process browser automation."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.automation.dependencies import get_automation_service
from app.automation.service import AutomationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/automation", tags=["automation"])


class AutomationStartResponse(BaseModel):
    status: str
    message: str


@router.post("/start", response_model=AutomationStartResponse)
async def start_automation(
    service: Annotated[AutomationService, Depends(get_automation_service)],
) -> AutomationStartResponse:
    """Start in-process automation."""
    try:
        await service.start()
    except Exception as exc:
        logger.exception("Failed to start automation")
        raise HTTPException(status_code=500, detail="Automation failed to start") from exc

    return AutomationStartResponse(status="success", message="Automation started")
