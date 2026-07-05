"""Seed default application setting definitions."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.settings.seeds.default_definitions import DEFAULT_SETTING_DEFINITIONS
from app.infrastructure.database.models import AppSettingDefinitionModel


async def seed_app_settings(session: AsyncSession) -> None:
    """Seed setting definitions if none exist."""
    result = await session.execute(select(AppSettingDefinitionModel.id).limit(1))
    if result.scalar_one_or_none():
        return

    for definition in DEFAULT_SETTING_DEFINITIONS:
        session.add(AppSettingDefinitionModel(**definition))

    await session.commit()
