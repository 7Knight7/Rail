"""Report 6 / scr-station handler: SCR Station Mode Unsatisfactory modal extraction."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.automation.report6_scr_filters import REPORT_6_SCR_FILTERS
from app.automation.reports import ReportDefinition
from app.automation.schemas import ReportResult
from app.automation.utils import log_automation_event
from app.automation.workflow import ingest_downloaded_file

from .report5_handler import Report5Handler

if TYPE_CHECKING:
    from playwright.async_api import Page

    from app.automation.session import SessionManager

logger = logging.getLogger(__name__)


class Report6Handler(Report5Handler):
    """Execute SCR Station Unsatisfactory workflow (canonical key: scr-station)."""

    expected_mode = "Station"

    async def execute(
        self,
        page: "Page",
        session: "SessionManager",
        report: ReportDefinition,
    ) -> ReportResult:
        page = await self.ensure_mis_page(page, session, f"{report.slug}_start")
        await self.navigation.navigate_to_report(page, report)
        page = await self.ensure_mis_page(page, session, f"{report.slug}_after_nav")

        report_root, _, _ = await self.apply_filters_and_submit(
            page, report, filters=REPORT_6_SCR_FILTERS, session=session
        )
        await self.click_received_twice(report_root, page, feedback=True)

        expected_count, complaints, error = await self._extract_scr_complaints(
            page, report_root, report.slug
        )

        page = await self.ensure_mis_page(page, session, f"{report.slug}_after_modal")

        if error:
            return self.build_failed_result(report.slug, error)

        csv_path = self._save_complaints_csv(complaints, report.slug)
        source_paths = [str(csv_path)]
        row_counts = {"unsatisfactory": len(complaints), "expected": expected_count}

        if len(complaints) != expected_count:
            return self.build_failed_result(
                report.slug,
                f"Count mismatch: expected {expected_count}, got {len(complaints)}",
                partial=bool(complaints),
                source_paths=source_paths,
                row_counts=row_counts,
                source_csv_path=str(csv_path),
                source_row_count=len(complaints),
            )

        ingestion_success = await ingest_downloaded_file(
            csv_path,
            report.slug,
            source="scr_modal_csv",
        )

        if not ingestion_success:
            return self.build_failed_result(
                report.slug,
                "Ingestion failed",
                partial=True,
                source_paths=source_paths,
                row_counts=row_counts,
                source_csv_path=str(csv_path),
                source_row_count=len(complaints),
            )

        archive_success, archive_path, _ = await self.archive_pdf(
            page, report_root, report.slug, session=session
        )
        processing_result = await self.invoke_processor(report.slug, ingestion_success)

        if not processing_result.success:
            return self.build_failed_result(
                report.slug,
                processing_result.error or "Processing failed",
                partial=True,
                source_paths=source_paths,
                row_counts=row_counts,
                ingestion_success=True,
                source_csv_path=str(csv_path),
                source_row_count=len(complaints),
            )

        log_automation_event(
            logger,
            "scr_station_complete",
            extracted_count=len(complaints),
            expected_count=expected_count,
        )

        return self.build_success_result(
            report.slug,
            source_paths=source_paths,
            row_counts=row_counts,
            excel_path=processing_result.excel_path,
            pdf_path=processing_result.pdf_path,
            archive_path=archive_path if archive_success else None,
            processor_used=processing_result.processor_used,
            input_row_count=len(complaints),
            processed_row_count=processing_result.processed_row_count,
            ingestion_success=True,
            source_csv_path=str(csv_path),
            source_row_count=len(complaints),
        )
