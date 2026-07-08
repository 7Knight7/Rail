"""Final output generation API."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse

from app.domain.entities.user import User
from app.features.auth.dependencies import get_current_active_user, require_officer_or_admin, validate_csrf_token
from app.features.outputs.dependencies import get_output_generation_service
from app.features.outputs.schemas import (
    GenerateOutputsRequest,
    GenerateOutputsResponse,
    GeneratedReportListResponse,
)
from app.features.outputs.service import OutputGenerationService

router = APIRouter(prefix="/outputs", tags=["outputs"])

MEDIA_TYPES = {
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
    "csv": "text/csv",
    "dashboard": "application/json",
    "dashboard_json": "application/json",
}


@router.get("/reports", response_model=GeneratedReportListResponse)
async def list_generated_reports(
    service: Annotated[OutputGenerationService, Depends(get_output_generation_service)],
    _user: Annotated[User, Depends(get_current_active_user)],
    search: str | None = Query(default=None),
    sort_by: str = Query(default="generatedAt", alias="sortBy"),
    sort_order: str = Query(default="desc", alias="sortOrder"),
) -> GeneratedReportListResponse:
    """List all generated report batches from the exports archive."""
    return service.list_reports(search=search, sort_by=sort_by, sort_order=sort_order)


@router.post("/generate", response_model=GenerateOutputsResponse)
async def generate_outputs(
    body: GenerateOutputsRequest,
    service: Annotated[OutputGenerationService, Depends(get_output_generation_service)],
    _user: Annotated[User, Depends(require_officer_or_admin)],
    _csrf: None = Depends(validate_csrf_token),
) -> GenerateOutputsResponse:
    """Generate final Excel, PDF, and dashboard JSON from a processed dataset."""
    return await service.generate(body)


@router.get("/{batch_id}/download")
async def download_output(
    batch_id: str,
    service: Annotated[OutputGenerationService, Depends(get_output_generation_service)],
    _user: Annotated[User, Depends(get_current_active_user)],
    format: str = Query(..., description="excel, pdf, or dashboard"),
) -> FileResponse:
    """Download a generated output artifact."""
    file_path = service.resolve_download_path(batch_id, format)
    media_type = MEDIA_TYPES.get(format, "application/octet-stream")
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type=media_type,
    )
