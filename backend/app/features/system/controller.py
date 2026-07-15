"""API controller for system info and maintenance actions (admin only)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.features.auth.dependencies import require_admin, validate_csrf_token
from app.features.system.schemas import ClearCacheResponse, SystemInfoResponse
from app.features.system.service import SystemService
from app.infrastructure.database.session import get_db_session

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info", response_model=SystemInfoResponse)
async def get_system_info(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _user: Annotated[User, Depends(require_admin)],
) -> SystemInfoResponse:
    """Live status of backend, database, CDP browser, automation, and storage."""
    return await SystemService(session).info()


@router.post(
    "/clear-cache",
    response_model=ClearCacheResponse,
    dependencies=[Depends(validate_csrf_token)],
)
async def clear_cache(
    user: Annotated[User, Depends(require_admin)],
) -> ClearCacheResponse:
    """Clear the settings cache and dashboard analytics cache."""
    from app.features.dashboard.analytics import clear_analytics_cache
    from app.features.settings.cache import settings_cache

    await settings_cache.invalidate_all()
    clear_analytics_cache()

    try:
        from app.features.activity.emit import emit_activity

        await emit_activity(
            user_id=user.id,
            action="CACHE_CLEARED",
            message="Cleared application caches",
            status="info",
        )
    except Exception:
        pass

    return ClearCacheResponse(cleared=["settings", "dashboard_analytics"])
