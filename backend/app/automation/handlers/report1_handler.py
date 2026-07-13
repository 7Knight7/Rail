"""Report 1 handler: dual-source Zone Wise + Feedback workflow."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

from app.automation.config import config
from app.automation.downloader import ReportDownloader
from app.automation.pdf_archiver import PdfArchiver
from app.automation.report1_filters import REPORT_1_FILTERS
from app.automation.reports import ReportDefinition
from app.automation.run_context import get_run_context
from app.automation.schemas import ReportResult
from app.automation.table_extractor import TableExtractor
from app.automation.utils import log_automation_event, resolve_report_dir
from app.automation.workflow import (
    FEEDBACK_DATASET_ID,
    extract_feedback_zone_csv,
    extract_with_retry,
    ingest_downloaded_file,
    regenerate_comprehensive_for_pdf,
)

from .base import BaseReportHandler

if TYPE_CHECKING:
    from playwright.async_api import Page

    from app.automation.session import SessionManager

logger = logging.getLogger(__name__)


class Report1Handler(BaseReportHandler):
    """Execute Report 1 dual-source Comprehensive + Feedback workflow."""

    async def execute(
        self,
        page: "Page",
        session: "SessionManager",
        report: ReportDefinition,
    ) -> ReportResult:
        ctx = get_run_context()
        page = await self.ensure_mis_page(page, session, f"{report.slug}_start")
        await self.navigation.navigate_to_report(page, report)
        page = await self.ensure_mis_page(page, session, f"{report.slug}_after_nav")

        report_root, _, row_count = await self.apply_filters_and_submit(
            page, report, session=session
        )
        await self.click_received_twice(report_root, page, report_slug=report.slug)

        extractor = TableExtractor(output_dir=Path(config.extracted_data_dir))
        t_extract = time.perf_counter()
        extraction_result, _, _ = await extract_with_retry(
            page,
            extractor,
            report_root,
            report,
            self.navigation,
            self.filter_service,
            self.discovery_service,
            self.generator,
            session,
            max_retries=1,
        )
        if ctx is not None:
            ctx.timing.record_report_span(
                "report1", "extraction", time.perf_counter() - t_extract
            )
            ctx.timing.spans["extraction:report1"] = round(
                time.perf_counter() - t_extract, 3
            )
            log_automation_event(
                logger,
                "report_extraction_completed",
                slug="report1",
                duration_seconds=round(time.perf_counter() - t_extract, 3),
            )

        source_paths: list[str] = []
        row_counts: dict[str, int] = {}

        if extraction_result.csv_path:
            source_paths.append(str(extraction_result.csv_path))
            row_counts["comprehensive"] = extraction_result.row_count

        page = await self.ensure_mis_page(page, session, "feedback_extraction")
        feedback_cm = (
            ctx.timing.report_span("report1", "feedback_extraction")
            if ctx is not None
            else None
        )

        async def _feedback():
            return await extract_feedback_zone_csv(
                page,
                extractor,
                self.navigation,
                self.filter_service,
                self.discovery_service,
                self.generator,
                session,
                max_retries=1,
            )

        if feedback_cm is not None:
            with feedback_cm:
                feedback_result, _, _ = await _feedback()
        else:
            feedback_result, _, _ = await _feedback()

        feedback_ingestion_success = False
        if feedback_result.success and feedback_result.csv_path:
            source_paths.append(str(feedback_result.csv_path))
            row_counts["feedback"] = feedback_result.row_count
            feedback_ingestion_success = await ingest_downloaded_file(
                feedback_result.csv_path,
                FEEDBACK_DATASET_ID,
                source="feedback_zone_csv",
            )

        page = await self.ensure_mis_page(page, session, "comprehensive_regenerate")
        report_root, _, _ = await regenerate_comprehensive_for_pdf(
            page,
            self.navigation,
            self.filter_service,
            self.discovery_service,
            self.generator,
            extractor,
            session,
            known_filters=list(REPORT_1_FILTERS),
        )

        ingestion_success = False
        if extraction_result.success and extraction_result.csv_path:
            ingestion_success = await ingest_downloaded_file(
                extraction_result.csv_path,
                report.slug,
                source="html_extracted_csv",
            )

        archive_path: str | None = None
        downloader = ReportDownloader(downloads_dir=Path(config.downloads_dir))
        pdf_cm = (
            ctx.timing.report_span("report1", "phase6_pdf_download")
            if ctx is not None
            else None
        )

        async def _download():
            return await downloader.download_report(
                report_root, page, report_slug=report.slug
            )

        if pdf_cm is not None:
            with pdf_cm:
                download_result = await _download()
        else:
            download_result = await _download()

        phase6_pdf_path = None
        if download_result.file_path and download_result.file_path.suffix.lower() == ".pdf":
            phase6_pdf_path = download_result.file_path

        page = await self.ensure_mis_page(page, session, "pdf_archive")
        archive_dir = resolve_report_dir(config.pdf_archive_dir, report.slug)
        archiver = PdfArchiver(archive_dir=archive_dir)
        archive_cm = (
            ctx.timing.report_span("report1", "archive") if ctx is not None else None
        )

        async def _archive():
            return await archiver.archive_pdf(
                page,
                report_root,
                report.slug,
                use_print=False,
                existing_pdf_path=phase6_pdf_path,
            )

        if archive_cm is not None:
            with archive_cm:
                archive_result = await _archive()
        else:
            archive_result = await _archive()
        if archive_result.file_path:
            archive_path = str(archive_result.file_path)

        phase8_ready = (
            extraction_result.success
            and feedback_result.success
            and ingestion_success
            and feedback_ingestion_success
        )

        if not phase8_ready:
            return self.build_failed_result(
                report.slug,
                "Phase 8 blocked: validated Comprehensive and Feedback sources required",
                partial=ingestion_success or feedback_ingestion_success,
                source_paths=source_paths,
                row_counts=row_counts,
                ingestion_success=ingestion_success,
            )

        t_proc = time.perf_counter()
        processing_result = await self.invoke_processor(report.slug, ingestion_success)
        if ctx is not None:
            elapsed = time.perf_counter() - t_proc
            ctx.timing.record_report_span("report1", "processing", elapsed)
            ctx.timing.record_report_span("report1", "excel_generation", elapsed / 2)
            ctx.timing.record_report_span("report1", "pdf_generation", elapsed / 2)
            ctx.timing.spans["processing:report1"] = round(elapsed, 3)

        if not processing_result.success:
            return self.build_failed_result(
                report.slug,
                processing_result.error or "Processing failed",
                partial=True,
                source_paths=source_paths,
                row_counts=row_counts,
                ingestion_success=ingestion_success,
            )

        log_automation_event(
            logger,
            "report1_complete",
            row_count=row_count,
            comprehensive_rows=extraction_result.row_count,
            feedback_rows=feedback_result.row_count,
        )

        return self.build_success_result(
            report.slug,
            source_paths=source_paths,
            row_counts=row_counts,
            excel_path=processing_result.excel_path,
            pdf_path=processing_result.pdf_path,
            archive_path=archive_path,
            processor_used=processing_result.processor_used,
            input_row_count=processing_result.input_row_count,
            processed_row_count=processing_result.processed_row_count,
            ingestion_success=ingestion_success,
            source_csv_path=str(extraction_result.csv_path) if extraction_result.csv_path else None,
            source_row_count=extraction_result.row_count,
        )
