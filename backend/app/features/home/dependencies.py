from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.home.service import HomeOverviewService
from app.infrastructure.database.session import get_db_session


def get_home_overview_service(
    session: AsyncSession = Depends(get_db_session),
) -> HomeOverviewService:
    return HomeOverviewService(session)
