from fastapi import APIRouter

from app.features.auth.controller import router as auth_router
from app.features.health.controller import router as health_router
from app.features.rules.controller import router as rules_router
from app.features.automation.controller import router as automation_router
from app.features.settings.controller import router as settings_router
from app.features.summary.controller import router as summary_router
from app.features.templates.controller import router as templates_router
from app.features.datasets.controller import router as datasets_router
from app.features.processing.controller import router as processing_router
from app.features.dashboard.controller import router as dashboard_router
from app.features.home.controller import router as home_router
from app.features.report_configs.controller import router as report_configs_router
from app.features.outputs.controller import router as outputs_router
from app.features.uploads.controller import router as uploads_router
from app.features.workflows.controller import router as workflows_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(workflows_router)
api_router.include_router(uploads_router)
api_router.include_router(datasets_router)
api_router.include_router(processing_router)
api_router.include_router(dashboard_router)
api_router.include_router(outputs_router)
api_router.include_router(home_router)
api_router.include_router(report_configs_router)
api_router.include_router(templates_router)
api_router.include_router(rules_router)
api_router.include_router(summary_router)
api_router.include_router(settings_router)
api_router.include_router(automation_router)
