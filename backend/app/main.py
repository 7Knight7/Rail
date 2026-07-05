from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.error_handlers import register_error_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.core.security.headers import SecurityHeadersMiddleware
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.seed.seed_automation_profiles import seed_automation_profiles
from app.infrastructure.seed.seed_app_settings import seed_app_settings
from app.infrastructure.seed.seed_prompt_templates import seed_prompt_templates
from app.infrastructure.seed.seed_users import seed_admin_user
from app.infrastructure.seed.seed_workflows import seed_workflows


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    async with SessionLocal() as session:
        await seed_workflows(session)
        await seed_admin_user(session)
        await seed_prompt_templates(session)
        await seed_app_settings(session)
        await seed_automation_profiles(session)
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
    expose_headers=["X-Request-ID"],
)

register_error_handlers(app)
app.include_router(api_router, prefix=settings.api_prefix)
