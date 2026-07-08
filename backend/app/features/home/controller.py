"""Home overview API."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.domain.entities.user import User
from app.features.auth.dependencies import get_current_active_user
from app.features.home.dependencies import get_home_overview_service
from app.features.home.schemas import HomeOverviewResponse
from app.features.home.service import HomeOverviewService

router = APIRouter(prefix="/home", tags=["home"])


@router.get("/overview", response_model=HomeOverviewResponse)
async def get_home_overview(
    service: Annotated[HomeOverviewService, Depends(get_home_overview_service)],
    _user: Annotated[User, Depends(get_current_active_user)],
) -> HomeOverviewResponse:
    return await service.get_overview()
