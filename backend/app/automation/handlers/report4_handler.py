"""Report 4 / types handler: 7 complaint Types x Top 10 each."""

from __future__ import annotations

import csv
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from app.automation.config import config
from app.automation.report1_filters import FilterFieldDefinition
from app.automation.report4_filters import (
    get_report4_filters_for_type,
    get_type_configs,
)
from app.automation.reports import ReportDefinition
from app.automation.schemas import ReportResult
from app.automation.table_extractor import TableExtractor
from app.automation.utils import ensure_directory, log_automation_event, resolve_report_dir

from .base import BaseReportHandler

if TYPE_CHECKING:
    from playwright.async_api import Page

    from app.automation.session import SessionManager

logger = logging.getLogger(__name__)


class Report4Handler(BaseReportHandler):
    """Execute cause-wise Top 10 per Type workflow (canonical key: types)."""

    async def execute(
        self,
        page: "Page",
        session: "SessionManager",
        report: ReportDefinition,
    ) -> ReportResult:
        started_at = datetime.now(UTC).isoformat()
        t0 = time.perf_counter()
        page = await self.ensure_mis_page(page, session, f"{report.slug}_start")
        type_configs = get_type_configs()
        source_paths: list[str] = []
        row_counts: dict[str, int] = {}
        total_rows = 0

        extracted_dir = ensure_directory(
            resolve_report_dir(config.extracted_data_dir, report.slug)
        )

        # Navigate to Tab 10 / report16 once
        await self.navigation.navigate_to_report(page, report)
        page = await self.ensure_mis_page(page, session, f"{report.slug}_after_nav")
        try:
            await page.wait_for_selector("#complaintTypeInput, #viewType", timeout=15000)
        except Exception:
            pass

        # First type: apply full base filters + type
        first = type_configs[0]
        filters = get_report4_filters_for_type(first.name)
        report_root, _, _ = await self.apply_filters_and_submit(
            page, report, filters=filters, session=session
        )
        if not await self._sort_or_skip(report_root, page, report.slug, first.name):
            pass
        else:
            total_rows += await self._extract_type(
                report_root, report, first, extracted_dir, source_paths, row_counts
            )

        # Remaining types: change Type only, stay on report16
        for type_config in type_configs[1:]:
            page = await self.ensure_mis_page(
                page, session, f"{report.slug}_{type_config.name}"
            )
            type_only = [
                FilterFieldDefinition(
                    name="type",
                    selector="#complaintTypeInput",
                    field_type="select",
                    value=type_config.portal_value,
                    required=True,
                    label="Type",
                )
            ]
            report_root, _, _ = await self.apply_filters_and_submit(
                page, report, filters=type_only, session=session
            )
            # Wait for regenerated table before sort (type-only Submit can lag)
            try:
                await page.locator("th:has-text('Received'), td:has-text('Received')").first.wait_for(
                    state="visible", timeout=15_000
                )
            except Exception:
                log_automation_event(
                    logger,
                    "types_received_header_wait_timeout",
                    type_name=type_config.name,
                )
            if not await self._sort_or_skip(
                report_root, page, report.slug, type_config.name
            ):
                continue
            total_rows += await self._extract_type(
                report_root, report, type_config, extracted_dir, source_paths, row_counts
            )

        if not source_paths:
            return self.build_failed_result(
                report.slug,
                "No complaint type data extracted",
            )

        combined_path = extracted_dir / "types_combined_index.csv"
        with combined_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["type_name", "csv_path", "row_count"])
            for type_config in type_configs:
                type_slug = (
                    type_config.name.lower().replace(" ", "_").replace("&", "and")
                )
                path = extracted_dir / f"report4_{type_slug}_raw.csv"
                if path.exists():
                    writer.writerow(
                        [type_config.name, str(path), row_counts.get(type_config.name, 0)]
                    )

        extraction_seconds = time.perf_counter() - t0
        log_automation_event(
            logger,
            "report_extraction_completed",
            slug=report.slug,
            type_count=len(source_paths),
            total_rows=total_rows,
            duration_seconds=round(extraction_seconds, 3),
        )
        return await self.finalize_after_extract(
            slug=report.slug,
            csv_path=combined_path,
            source_paths=source_paths,
            row_counts=row_counts,
            source_row_count=total_rows,
            started_at=started_at,
            extraction_seconds=round(extraction_seconds, 3),
        )

    async def _sort_or_skip(
        self,
        report_root,
        page: "Page",
        report_slug: str,
        type_name: str,
    ) -> bool:
        """Sort Received descending; return False if header missing (skip type)."""
        from app.automation.table_sort import ReceivedSortError

        try:
            await self.click_received_twice(
                report_root, page, report_slug=report_slug
            )
            return True
        except ReceivedSortError as exc:
            log_automation_event(
                logger,
                "types_sort_skipped",
                type_name=type_name,
                error=str(exc),
            )
            return False

    async def _extract_type(
        self,
        report_root,
        report: ReportDefinition,
        type_config,
        extracted_dir: Path,
        source_paths: list[str],
        row_counts: dict[str, int],
    ) -> int:
        extractor = TableExtractor(output_dir=extracted_dir)
        extraction_result = await extractor.extract_and_save(report_root, report.slug)

        if (
            await self.reject_empty_table(extraction_result)
            or not extraction_result.data
        ):
            log_automation_event(
                logger,
                "types_type_extraction_failed",
                type_name=type_config.name,
                error=extraction_result.error,
            )
            return 0

        data = extraction_result.data
        if len(data) > 11:
            data = data[:11]

        type_slug = (
            type_config.name.lower().replace(" ", "_").replace("&", "and")
        )
        csv_path = extracted_dir / f"report4_{type_slug}_raw.csv"
        self._save_type_csv(data, csv_path)
        source_paths.append(str(csv_path))
        row_counts[type_config.name] = max(len(data) - 1, 0)
        return row_counts[type_config.name]

    @staticmethod
    def _save_type_csv(data: list[list[str]], csv_path: Path) -> None:
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            for row in data:
                writer.writerow(row)
