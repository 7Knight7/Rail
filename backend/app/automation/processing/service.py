"""Phase 8 orchestration for post-ingestion report processing."""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import select

from app.automation.processing.base import ProcessingResult
from app.automation.processing.registry import PROCESSORS
from app.automation.report_keys import canonicalize_report_key
from app.automation.utils import log_automation_event
from app.infrastructure.database.session import SessionLocal

logger = logging.getLogger(__name__)

FEEDBACK_DATASET_ID = "report1_feedback"


async def process_report(report_slug: str, ingestion_success: bool) -> ProcessingResult:
    """Run Phase 8 processing when ingestion succeeded."""
    if not ingestion_success:
        return ProcessingResult(attempted=False, success=False)

    canonical = canonicalize_report_key(report_slug)
    processor = PROCESSORS.get(canonical)
    if processor is None:
        return ProcessingResult(
            attempted=True,
            success=False,
            error=f"No processor registered for report slug: {report_slug}",
        )

    log_automation_event(
        logger,
        "phase8_started",
        report_slug=canonical,
        processor=processor.processor_name,
    )

    try:
        async with SessionLocal() as session:
            from app.features.datasets.service import DatasetService
            from app.infrastructure.database.models import ReportDatasetModel

            dataset_service = DatasetService(session)
            await dataset_service.ensure_dataset_exists(canonical)

            result = await session.execute(
                select(ReportDatasetModel)
                .where(ReportDatasetModel.report_id == canonical)
                .limit(1)
            )
            model = result.scalar_one_or_none()
            if model is None or not model.source_file_path:
                return ProcessingResult(
                    attempted=True,
                    success=False,
                    processor_used=processor.processor_name,
                    error=f"Dataset missing for report: {canonical}",
                )

            source_a_path = Path(model.source_file_path)
            if source_a_path.suffix.lower() == ".pdf":
                return ProcessingResult(
                    attempted=True,
                    success=False,
                    processor_used=processor.processor_name,
                    error="PDF cannot be used as processing input",
                    source_a_path=str(source_a_path),
                )

            source_b_path: Path | None = None
            if canonical == "report1":
                feedback_result = await session.execute(
                    select(ReportDatasetModel)
                    .where(ReportDatasetModel.report_id == FEEDBACK_DATASET_ID)
                    .limit(1)
                )
                feedback_model = feedback_result.scalar_one_or_none()
                if feedback_model and feedback_model.source_file_path:
                    candidate = Path(feedback_model.source_file_path)
                    if candidate.exists() and candidate.suffix.lower() != ".pdf":
                        source_b_path = candidate

            processing_result = processor.process(
                source_a_path=source_a_path,
                report_slug=canonical,
                source_b_path=source_b_path,
            )
            processing_result.attempted = True
            processing_result.processor_used = processor.processor_name

            if processing_result.success:
                log_automation_event(
                    logger,
                    "phase8_completed",
                    excel_path=processing_result.excel_path,
                    pdf_path=processing_result.pdf_path,
                    processed_row_count=processing_result.processed_row_count,
                    source_a_path=processing_result.source_a_path,
                    source_b_path=processing_result.source_b_path,
                    source_a_rows=processing_result.source_a_rows,
                    source_b_rows=processing_result.source_b_rows,
                )
            else:
                log_automation_event(
                    logger,
                    "phase8_failed",
                    error=processing_result.error,
                )

            return processing_result

    except Exception as exc:
        logger.exception("Phase 8 processing failed")
        log_automation_event(logger, "phase8_error", error=str(exc))
        return ProcessingResult(
            attempted=True,
            success=False,
            processor_used=processor.processor_name if processor else None,
            error=str(exc),
        )
