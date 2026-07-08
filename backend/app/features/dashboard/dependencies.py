from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.dashboard.service import DashboardService
from app.infrastructure.database.session import get_db_session


def get_dashboard_service(
    session: AsyncSession = Depends(get_db_session),
) -> DashboardService:
    return DashboardService(session)
