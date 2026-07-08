from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.processing.service import ReportProcessingService
from app.infrastructure.database.session import get_db_session


def get_report_processing_service(
    session: AsyncSession = Depends(get_db_session),
) -> ReportProcessingService:
    return ReportProcessingService(session)
