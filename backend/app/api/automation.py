"""API routes for in-process browser automation."""

import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.automation.config import config
from app.automation.dependencies import get_automation_service
from app.automation.report_keys import canonicalize_report_key
from app.automation.schemas import MultiReportResult
from app.automation.service import AutomationService
from app.domain.entities.user import User
from app.features.auth.dependencies import require_admin, validate_csrf_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/automation", tags=["automation"])

ALLOWED_PDF_KEYS = frozenset(
    {
        "report1",
        "division",
        "train-no",
        "types",
        "scr-train",
        "scr-station",
    }
)


def _resolve_latest_pdf(report_key: str) -> Path:
    """Resolve the newest PDF under storage/output/pdf/{canonical_key}/."""
    canonical = canonicalize_report_key(report_key)
    if canonical not in ALLOWED_PDF_KEYS:
        raise HTTPException(status_code=404, detail=f"Unknown report key: {report_key}")

    base = Path(config.output_pdf_dir).resolve()
    report_dir = (base / canonical).resolve()
    if not str(report_dir).startswith(str(base)):
        raise HTTPException(status_code=400, detail="Invalid report path")
    if not report_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"No PDF directory for {canonical}")

    pdfs = sorted(report_dir.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not pdfs:
        raise HTTPException(status_code=404, detail=f"No PDF found for {canonical}")

    pdf_path = pdfs[0]
    if pdf_path.stat().st_size <= 0:
        raise HTTPException(status_code=404, detail=f"PDF empty for {canonical}")

    header = pdf_path.read_bytes()[:5]
    if header != b"%PDF-":
        raise HTTPException(status_code=500, detail=f"Invalid PDF header for {canonical}")

    return pdf_path


@router.post(
    "/start",
    response_model=MultiReportResult,
    dependencies=[Depends(require_admin), Depends(validate_csrf_token)],
)
async def start_automation(
    service: Annotated[AutomationService, Depends(get_automation_service)],
    _user: Annotated[User, Depends(require_admin)],
) -> MultiReportResult:
    """Connect to Chrome via CDP and run all catalog reports."""
    try:
        result = await service.start()
    except Exception as exc:
        logger.exception("Unexpected automation start failure")
        raise HTTPException(status_code=500, detail="Automation failed to start") from exc

    logger.info(
        "Automation start completed: success=%s connected=%s tab_found=%s report_count=%s",
        result.success,
        result.connected,
        result.tab_found,
        len(result.reports),
    )
    return result


@router.get(
    "/reports/{report_key}/pdf",
    dependencies=[Depends(require_admin)],
)
async def download_report_pdf(
    report_key: str,
    _user: Annotated[User, Depends(require_admin)],
) -> FileResponse:
    """Download the latest final PDF for a report (restricted to storage/output/pdf)."""
    pdf_path = _resolve_latest_pdf(report_key)
    logger.info("Serving PDF for %s: %s", report_key, pdf_path)
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name,
        content_disposition_type="attachment",
    )
