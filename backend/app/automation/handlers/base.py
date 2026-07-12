"""Base handler class with shared automation logic."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.automation.config import config
from app.automation.filters import FilterDiscoveryService, FilterService
from app.automation.generator import ReportGenerationError, ReportGeneratorService
from app.automation.navigation import NavigationService
from app.automation.pdf_archiver import PdfArchiver
from app.automation.processing.service import process_report
from app.automation.report1_filters import build_filters_from_discovery
from app.automation.report_keys import canonicalize_report_key, pdf_download_url
from app.automation.reports import ReportDefinition
from app.automation.schemas import ReportResult
from app.automation.session import MisSessionError, SessionManager
from app.automation.table_extractor import ExtractionResult, TableExtractor
from app.automation.table_sort import ReceivedColumnService
from app.automation.utils import log_automation_event, resolve_report_dir

if TYPE_CHECKING:
    from playwright.async_api import Browser, Page

logger = logging.getLogger(__name__)

# Re-export for handlers/tests that imported from base
__all__ = ["BaseReportHandler", "MisSessionError"]


class BaseReportHandler(ABC):
    """Base class for report-specific handlers."""

    def __init__(self) -> None:
        self.navigation = NavigationService()
        self.filter_service = FilterService()
        self.discovery_service = FilterDiscoveryService()
        self.generator = ReportGeneratorService()
        self.received_service = ReceivedColumnService()
        self._browser: Browser | None = None

    def bind_browser(self, browser: "Browser") -> None:
        """Attach the CDP browser so session reacquisition can scan all tabs."""
        self._browser = browser

    @abstractmethod
    async def execute(
        self,
        page: "Page",
        session: SessionManager,
        report: ReportDefinition,
    ) -> ReportResult:
        """Execute the report workflow and return result."""
        ...

    async def ensure_mis_page(
        self,
        page: "Page",
        session: SessionManager,
        context: str = "operation",
    ) -> "Page":
        """Reacquire authenticated MIS page; raise MisSessionError only if none exists."""
        if self._browser is not None:
            mis_page = await session.ensure_authenticated_mis_page(
                self._browser,
                page,
            )
            log_automation_event(logger, "mis_session_verified", context=context)
            return mis_page

        status = await session.verify_mis_session(page)
        if not status.valid:
            log_automation_event(
                logger,
                "mis_session_lost",
                context=context,
                error_code=status.error_code,
                error=status.error,
            )
            raise MisSessionError(status)
        log_automation_event(logger, "mis_session_verified", context=context)
        return page

    async def verify_session(
        self,
        page: "Page",
        session: SessionManager,
        context: str = "operation",
    ) -> "Page":
        """Verify MIS session is valid; reacquire when browser is bound."""
        return await self.ensure_mis_page(page, session, context)

    async def apply_filters_and_submit(
        self,
        page: "Page",
        report: ReportDefinition,
        filters: list | None = None,
        session: SessionManager | None = None,
    ) -> tuple:
        """Apply filters, submit, and verify report is displayed.

        Returns (report_root, applied_values, row_count).
        """
        if session is not None:
            page = await self.ensure_mis_page(page, session, f"{report.slug}_before_submit")

        report_root = await self.filter_service.get_report_root(page)

        if filters is None:
            discovered_fields = await self.discovery_service.discover_fields(page)
            filters = build_filters_from_discovery(discovered_fields, report.slug)

        applied_values = await self.filter_service.apply_filters(
            report_root,
            filters,
            page=page,
        )
        await self.filter_service.validate_mandatory(report_root, filters, applied_values)

        # Verify Previous Day was applied when dateRange is present
        date_applied = None
        for name, value in applied_values.items():
            if "date" in name.lower() and "range" in name.lower():
                date_applied = value
                break
        if date_applied is None:
            date_applied = applied_values.get("dateRange")
        if date_applied and "previous day" not in str(date_applied).lower():
            log_automation_event(
                logger,
                "date_range_mismatch",
                applied=date_applied,
                expected="Previous Day",
            )
            raise ReportGenerationError(
                f"Date Range must be Previous Day before Submit, got: {date_applied}"
            )

        await self.generator.generate_report(report_root, page)
        row_count = await self.generator.count_rows(report_root)

        if not await self.generator.verify_report_displayed(report_root):
            raise ReportGenerationError(f"Report {report.slug} did not display after generate")

        return report_root, applied_values, row_count

    async def click_received_twice(
        self,
        report_root: Any,
        page: "Page",
        feedback: bool = False,
    ) -> None:
        """Click Received or Feedback Received column header twice for descending sort."""
        if feedback:
            await self.received_service.sort_feedback_received_descending(report_root, page)
        else:
            await self.received_service.sort_received_descending(report_root, page)

    async def extract_table_data(
        self,
        page: "Page",
        report_root: Any,
        report_slug: str,
        required_headers: set[str] | None = None,
    ) -> ExtractionResult:
        """Extract HTML table data and save as CSV under the canonical key."""
        key = canonicalize_report_key(report_slug)
        extractor = TableExtractor(output_dir=Path(config.extracted_data_dir))

        if required_headers:
            data = await extractor.extract_table_data_by_headers(
                report_root,
                required_headers,
            )
            if not data:
                return ExtractionResult(
                    success=False,
                    error=f"Table with required headers not found for {key}",
                )
            html = await extractor.extract_table_html(report_root)
            csv_path = await extractor.save_as_csv_fixed(
                data,
                report_slug=key,
            )
            return ExtractionResult(
                success=csv_path is not None,
                html=html,
                data=data,
                csv_path=csv_path,
                row_count=len(data),
                column_count=len(data[0]) if data else 0,
            )
        return await extractor.extract_and_save(report_root, key)

    async def reject_empty_table(self, extraction_result: ExtractionResult) -> bool:
        """Check if table is empty or has no data. Returns True if should reject."""
        if not extraction_result.success:
            return True
        if extraction_result.row_count is None or extraction_result.row_count == 0:
            return True
        if extraction_result.data and len(extraction_result.data) == 0:
            return True
        if extraction_result.html and "no data available" in extraction_result.html.lower():
            return True
        return False

    async def ingest_csv(
        self,
        csv_path: Path,
        report_slug: str,
        source: str = "html_extracted_csv",
    ) -> bool:
        """Ingest the CSV file using the canonical dataset key."""
        from app.automation.workflow import ingest_downloaded_file

        return await ingest_downloaded_file(csv_path, report_slug, source)

    async def invoke_processor(self, report_slug: str, ingestion_success: bool):
        """Call the registered processor for this report slug."""
        return await process_report(canonicalize_report_key(report_slug), ingestion_success)

    async def archive_pdf(
        self,
        page: "Page",
        report_root: Any,
        report_slug: str,
        existing_pdf_path: Path | None = None,
        session: SessionManager | None = None,
    ) -> tuple[bool, str | None, str | None]:
        """Archive PDF for the report. Returns (success, archive_path, error)."""
        key = canonicalize_report_key(report_slug)
        if session is not None:
            page = await self.ensure_mis_page(page, session, f"{key}_before_pdf")

        archive_dir = resolve_report_dir(config.pdf_archive_dir, key)
        try:
            archiver = PdfArchiver(archive_dir=archive_dir)
            archive_result = await archiver.archive_pdf(
                page,
                report_root,
                key,
                use_print=False,
                existing_pdf_path=existing_pdf_path,
            )
            if self._browser is not None and session is not None:
                page = await session.ensure_authenticated_mis_page(self._browser, page)
            return (
                archive_result.success,
                str(archive_result.file_path) if archive_result.file_path else None,
                archive_result.error,
            )
        except Exception as exc:
            logger.warning("PDF archive failed for %s: %s", key, exc)
            return False, None, str(exc)

    def build_success_result(
        self,
        slug: str,
        *,
        source_paths: list[str] | None = None,
        row_counts: dict[str, int] | None = None,
        excel_path: str | None = None,
        pdf_path: str | None = None,
        archive_path: str | None = None,
        processor_used: str | None = None,
        input_row_count: int | None = None,
        processed_row_count: int | None = None,
        ingestion_success: bool = True,
        source_csv_path: str | None = None,
        source_row_count: int | None = None,
    ) -> ReportResult:
        """Build a successful ReportResult with download URL."""
        key = canonicalize_report_key(slug)
        csv_path = source_csv_path or (source_paths[0] if source_paths else None)
        row_count = source_row_count
        if row_count is None and row_counts:
            row_count = next(iter(row_counts.values()), None)
        return ReportResult(
            slug=key,
            dataset_key=key,
            status="success",
            source_paths=source_paths or [],
            source_csv_path=csv_path,
            source_row_count=row_count,
            row_counts=row_counts or {},
            ingestion_success=ingestion_success,
            excel_path=excel_path,
            pdf_path=pdf_path,
            pdf_download_url=pdf_download_url(key) if pdf_path else None,
            archive_path=archive_path,
            processing_attempted=True,
            processing_success=True,
            processor_used=processor_used,
            input_row_count=input_row_count,
            processed_row_count=processed_row_count,
        )

    def build_failed_result(
        self,
        slug: str,
        error: str,
        *,
        partial: bool = False,
        source_paths: list[str] | None = None,
        row_counts: dict[str, int] | None = None,
        ingestion_success: bool = False,
        source_csv_path: str | None = None,
        source_row_count: int | None = None,
    ) -> ReportResult:
        """Build a failed ReportResult."""
        key = canonicalize_report_key(slug)
        return ReportResult(
            slug=key,
            dataset_key=key,
            status="partial_success" if partial else "failed",
            source_paths=source_paths or [],
            source_csv_path=source_csv_path or (source_paths[0] if source_paths else None),
            source_row_count=source_row_count,
            row_counts=row_counts or {},
            ingestion_success=ingestion_success,
            error=error,
        )

    def build_skipped_result(self, slug: str, reason: str) -> ReportResult:
        """Build a skipped ReportResult."""
        key = canonicalize_report_key(slug)
        return ReportResult(
            slug=key,
            dataset_key=key,
            status="skipped",
            error=reason,
        )
