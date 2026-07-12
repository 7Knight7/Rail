"""Report 4 / types handler: 7 complaint Types x Top 10 each."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from app.automation.config import config
from app.automation.report4_filters import get_report4_filters_for_type, get_type_configs
from app.automation.reports import ReportDefinition
from app.automation.schemas import ReportResult
from app.automation.table_extractor import TableExtractor
from app.automation.utils import ensure_directory, log_automation_event, resolve_report_dir
from app.automation.workflow import ingest_downloaded_file

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
        page = await self.ensure_mis_page(page, session, f"{report.slug}_start")
        type_configs = get_type_configs()
        source_paths: list[str] = []
        row_counts: dict[str, int] = {}
        total_rows = 0

        extracted_dir = ensure_directory(
            resolve_report_dir(config.extracted_data_dir, report.slug)
        )

        for type_config in type_configs:
            page = await self.ensure_mis_page(
                page, session, f"{report.slug}_{type_config.name}"
            )
            await self.navigation.navigate_to_report(page, report)
            try:
                await page.wait_for_selector("select", timeout=15000)
                await page.wait_for_timeout(1000)
            except Exception:
                pass

            filters = get_report4_filters_for_type(type_config.name)
            report_root, _, _ = await self.apply_filters_and_submit(
                page, report, filters=filters, session=session
            )
            await self.click_received_twice(report_root, page)

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
                continue

            # Top 10 data rows (+ header)
            data = extraction_result.data
            if len(data) > 11:
                data = data[:11]

            type_slug = (
                type_config.name.lower()
                .replace(" ", "_")
                .replace("&", "and")
            )
            # Keep legacy filename prefix report4_ for processor discovery, under types/
            csv_path = extracted_dir / f"report4_{type_slug}_raw.csv"
            self._save_type_csv(data, csv_path)

            source_paths.append(str(csv_path))
            row_counts[type_config.name] = max(len(data) - 1, 0)
            total_rows += row_counts[type_config.name]

        if not source_paths:
            return self.build_failed_result(
                report.slug,
                "No complaint type data extracted",
            )

        # Ingest a combined index CSV so the dataset row points at types folder data
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

        ingestion_success = await ingest_downloaded_file(
            combined_path,
            report.slug,
            source="html_extracted_csv",
        )

        if not ingestion_success:
            return self.build_failed_result(
                report.slug,
                "Ingestion failed",
                partial=True,
                source_paths=source_paths,
                row_counts=row_counts,
                source_csv_path=str(combined_path),
                source_row_count=total_rows,
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
                source_csv_path=str(combined_path),
                source_row_count=total_rows,
            )

        log_automation_event(
            logger,
            "types_complete",
            type_count=len(source_paths),
            total_rows=total_rows,
        )

        return self.build_success_result(
            report.slug,
            source_paths=source_paths,
            row_counts=row_counts,
            excel_path=processing_result.excel_path,
            pdf_path=processing_result.pdf_path,
            processor_used=processing_result.processor_used,
            input_row_count=total_rows,
            processed_row_count=processing_result.processed_row_count,
            ingestion_success=True,
            source_csv_path=str(combined_path),
            source_row_count=total_rows,
        )

    @staticmethod
    def _save_type_csv(data: list[list[str]], csv_path: Path) -> None:
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            for row in data:
                writer.writerow(row)
