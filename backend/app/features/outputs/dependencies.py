from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.outputs.service import OutputGenerationService
from app.infrastructure.database.session import get_db_session


def get_output_generation_service(
    session: AsyncSession = Depends(get_db_session),
) -> OutputGenerationService:
    return OutputGenerationService(session)
