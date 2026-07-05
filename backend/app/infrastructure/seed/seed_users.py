import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.password import password_hasher
from app.infrastructure.database.models import UserModel

logger = logging.getLogger(__name__)

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_EMAIL = "admin@railway.gov.in"
DEFAULT_ADMIN_PASSWORD = "Admin@123456"


async def seed_admin_user(session: AsyncSession) -> None:
    existing = await session.execute(
        select(UserModel).where(UserModel.username == DEFAULT_ADMIN_USERNAME).limit(1)
    )
    if existing.scalar_one_or_none():
        logger.info("Admin user already exists, skipping")
        return

    logger.info("Creating default admin user")
    admin = UserModel(
        id=str(uuid.uuid4()),
        username=DEFAULT_ADMIN_USERNAME,
        email=DEFAULT_ADMIN_EMAIL,
        password_hash=password_hasher.hash(DEFAULT_ADMIN_PASSWORD),
        role="admin",
        is_active=True,
    )
    session.add(admin)
    await session.commit()
    logger.warning(
        "Default admin user created with password: %s - CHANGE THIS IMMEDIATELY IN PRODUCTION!",
        DEFAULT_ADMIN_PASSWORD,
    )
