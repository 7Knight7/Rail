from fastapi import APIRouter, Depends

from app.domain.entities.user import User
from app.features.auth.dependencies import get_current_active_user, require_officer_or_admin, validate_csrf_token
from app.features.processing.dependencies import get_report_processing_service
from app.features.processing.schemas import ProcessDatasetRequest, ProcessDatasetResponse
from app.features.processing.rules.schemas import ReportRuleSet, ReportRuleSetResponse
from app.features.processing.service import ReportProcessingService

router = APIRouter(prefix="/processing", tags=["processing"])


@router.get("/rules", response_model=ReportRuleSetResponse)
async def list_report_rules(
    service: ReportProcessingService = Depends(get_report_processing_service),
    _user: User = Depends(get_current_active_user),
) -> ReportRuleSetResponse:
    return service.list_report_rule_sets()


@router.get("/rules/{report_id}", response_model=ReportRuleSet)
async def get_report_rules(
    report_id: str,
    service: ReportProcessingService = Depends(get_report_processing_service),
    _user: User = Depends(get_current_active_user),
) -> ReportRuleSet:
    return service.get_report_rule_set(report_id)


@router.post("/execute", response_model=ProcessDatasetResponse)
async def execute_report_processing(
    body: ProcessDatasetRequest,
    service: ReportProcessingService = Depends(get_report_processing_service),
    _user: User = Depends(require_officer_or_admin),
    _csrf: None = Depends(validate_csrf_token),
) -> ProcessDatasetResponse:
    return await service.process(body)


@router.post("/preview", response_model=ProcessDatasetResponse)
async def preview_report_processing(
    body: ProcessDatasetRequest,
    service: ReportProcessingService = Depends(get_report_processing_service),
    user: User = Depends(get_current_active_user),
) -> ProcessDatasetResponse:
    return await service.process(body)
