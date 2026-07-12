"""Report 3 / train-no handler: Train No. Wise Top 20."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from app.automation.config import config
from app.automation.report3_filters import REPORT_3_FILTERS
from app.automation.reports import ReportDefinition
from app.automation.schemas import ReportResult
from app.automation.table_extractor import TableExtractor
from app.automation.utils import log_automation_event
from app.automation.workflow import extract_with_retry, ingest_downloaded_file

from .base import BaseReportHandler

if TYPE_CHECKING:
    from playwright.async_api import Page

    from app.automation.session import SessionManager

logger = logging.getLogger(__name__)


class Report3Handler(BaseReportHandler):
    """Execute Train No. Wise Top 20 workflow (canonical key: train-no)."""

    async def execute(
        self,
        page: "Page",
        session: "SessionManager",
        report: ReportDefinition,
    ) -> ReportResult:
        page = await self.ensure_mis_page(page, session, f"{report.slug}_start")
        await self.navigation.navigate_to_report(page, report)
        page = await self.ensure_mis_page(page, session, f"{report.slug}_after_nav")
        # Allow report form controls to finish rendering after navigation
        try:
            await page.wait_for_selector("select", timeout=15000)
            await page.wait_for_timeout(1500)
        except Exception:
            pass

        report_root, _, row_count = await self.apply_filters_and_submit(
            page, report, filters=REPORT_3_FILTERS, session=session
        )
        await self.click_received_twice(report_root, page)

        extractor = TableExtractor(output_dir=Path(config.extracted_data_dir))
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

        if await self.reject_empty_table(extraction_result) or not extraction_result.csv_path:
            return self.build_failed_result(
                report.slug,
                extraction_result.error or "Extraction failed or empty table",
            )

        if extraction_result.data and len(extraction_result.data) > 21:
            top_data = extraction_result.data[:21]
            csv_path = await extractor.save_as_csv(
                top_data,
                report_slug=report.slug,
            )
            if csv_path:
                extraction_result.csv_path = csv_path
                extraction_result.data = top_data
                extraction_result.row_count = len(top_data)

        ingestion_success = await ingest_downloaded_file(
            extraction_result.csv_path,
            report.slug,
            source="html_extracted_csv",
        )

        if not ingestion_success:
            return self.build_failed_result(
                report.slug,
                "Ingestion failed",
                partial=True,
                source_paths=[str(extraction_result.csv_path)],
                row_counts={"extracted": extraction_result.row_count},
                source_csv_path=str(extraction_result.csv_path),
                source_row_count=extraction_result.row_count,
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
                source_paths=[str(extraction_result.csv_path)],
                row_counts={"extracted": extraction_result.row_count},
                ingestion_success=True,
                source_csv_path=str(extraction_result.csv_path),
                source_row_count=extraction_result.row_count,
            )

        log_automation_event(
            logger,
            "train_no_complete",
            row_count=row_count,
            extracted_rows=extraction_result.row_count,
        )

        return self.build_success_result(
            report.slug,
            source_paths=[str(extraction_result.csv_path)],
            row_counts={"extracted": extraction_result.row_count},
            excel_path=processing_result.excel_path,
            pdf_path=processing_result.pdf_path,
            archive_path=archive_path if archive_success else None,
            processor_used=processing_result.processor_used,
            input_row_count=processing_result.input_row_count,
            processed_row_count=processing_result.processed_row_count,
            ingestion_success=True,
            source_csv_path=str(extraction_result.csv_path),
            source_row_count=extraction_result.row_count,
        )
