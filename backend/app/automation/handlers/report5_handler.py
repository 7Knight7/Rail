"""Report 5 handler: SCR Train Mode Unsatisfactory modal extraction."""

from __future__ import annotations

import csv
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from app.automation.config import config
from app.automation.formatting.scr import mode_matches
from app.automation.report5_filters import REPORT_5_FILTERS
from app.automation.reports import ReportDefinition
from app.automation.schemas import ReportResult
from app.automation.table_extractor import FEEDBACK_ZONE_REQUIRED_HEADERS
from app.automation.utils import ensure_directory, log_automation_event, resolve_report_dir
from app.automation.workflow import ingest_downloaded_file

from .base import BaseReportHandler

if TYPE_CHECKING:
    from playwright.async_api import Page

    from app.automation.session import SessionManager

logger = logging.getLogger(__name__)

ZONE_WISE_HEADERS = list(FEEDBACK_ZONE_REQUIRED_HEADERS)


class Report5Handler(BaseReportHandler):
    """Execute Report 5 SCR Train Unsatisfactory workflow."""

    expected_mode = "Train"

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
            page, report, filters=REPORT_5_FILTERS, session=session
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
            "scr_train_complete",
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

    async def _extract_scr_complaints(
        self,
        page: "Page",
        report_root,
        report_slug: str,
    ) -> tuple[int, list[dict[str, str]], str | None]:
        table = await self._find_zone_wise_table(report_root)
        if table is None:
            return 0, [], "Zone Wise table not found"

        expected_count, target_row_idx = await self._get_scr_unsatisfactory_target(table)
        if expected_count == 0 or target_row_idx is None:
            return 0, [], "SCR Unsatisfactory count is 0 or not found"

        if not await self._click_unsatisfactory_row(page, table, target_row_idx):
            return expected_count, [], "Failed to open complaints modal"

        complaints = await self._extract_modal_pages(page)
        await self._close_modal(page)

        # Prefer Mode-column filter; portal uses T/S (or Train/Station).
        if complaints and any(k.lower() == "mode" for k in complaints[0]):
            mode_key = next(k for k in complaints[0] if k.lower() == "mode")
            filtered = [
                row
                for row in complaints
                if self._mode_matches(row.get(mode_key, ""))
            ]
        else:
            filtered = complaints

        return expected_count, filtered, None

    def _mode_matches(self, mode_value: str) -> bool:
        """Match portal Mode codes (T/S) or full labels (Train/Station)."""
        return mode_matches(self.expected_mode, mode_value)

    async def _find_zone_wise_table(self, report_root):
        tables = report_root.locator("table")
        count = await tables.count()
        for idx in range(count):
            table = tables.nth(idx)
            headers = await self._extract_table_headers(table)
            if self._is_zone_wise_table(headers):
                return table
        return None

    async def _extract_table_headers(self, table) -> list[str]:
        headers: list[str] = []
        # Prefer explicit thead
        thead_cells = table.locator("thead tr").first.locator("th, td")
        if await table.locator("thead tr").count() > 0 and await thead_cells.count() > 0:
            for idx in range(await thead_cells.count()):
                headers.append((await thead_cells.nth(idx).inner_text()).strip())
            return headers

        # Fallback: first row that looks like headers
        first_row = table.locator("tr").first
        cells = first_row.locator("th, td")
        for idx in range(await cells.count()):
            headers.append((await cells.nth(idx).inner_text()).strip())
        return headers

    @staticmethod
    def _is_zone_wise_table(headers: list[str]) -> bool:
        joined = " | ".join(headers).lower()
        has_org = "organisation" in joined or "organization" in joined
        has_feedback = "feedback received" in joined
        has_unsat = "unsatisfactory" in joined
        # Department-wise table usually lists departments; still has Organisation header.
        # Prefer the first matching feedback table (zone/division view when Zone=SCR).
        return has_org and has_feedback and has_unsat

    def _column_index(self, headers: list[str], *names: str) -> int | None:
        lower = [h.lower() for h in headers]
        for name in names:
            for idx, header in enumerate(lower):
                if name.lower() == header or name.lower() in header:
                    return idx
        return None

    async def _get_scr_unsatisfactory_target(
        self, table
    ) -> tuple[int, int | None]:
        """Return (count, row_index) for SCR or Total row.

        When Zone is already South Central Railway, Zone Wise shows SCR divisions
        and the Total row holds the zone Unsatisfactory count.
        """
        headers = await self._extract_table_headers(table)
        org_idx = self._column_index(headers, "Organisation", "Organization")
        unsat_idx = self._column_index(headers, "Unsatisfactory")
        if org_idx is None or unsat_idx is None:
            # Common layout with leading S.No.
            org_idx = 1 if len(headers) > 1 else 0
            unsat_idx = 6 if len(headers) > 6 else 5

        rows = table.locator("tbody tr, tfoot tr")
        row_count = await rows.count()
        # If Total is outside tbody/tfoot, also scan all tr except header
        if row_count == 0:
            rows = table.locator("tr")
            row_count = await rows.count()
        total_row_idx: int | None = None
        total_count = 0
        scr_row_idx: int | None = None
        scr_count = 0

        start = 0
        # Skip header row if scanning all tr
        first_cells = rows.nth(0).locator("th, td") if row_count else None
        if first_cells is not None and await first_cells.count() > 0:
            first_text = (await first_cells.nth(0).inner_text()).strip().lower()
            if first_text in {"s.no.", "s.no", "organisation", "organization"}:
                start = 1

        for idx in range(start, row_count):
            row = rows.nth(idx)
            cells = row.locator("td")
            cell_count = await cells.count()
            if cell_count <= max(org_idx, unsat_idx):
                continue
            org_text = (await cells.nth(org_idx).inner_text()).strip()
            unsat_text = (await cells.nth(unsat_idx).inner_text()).strip()
            digits = re.sub(r"[^\d]", "", unsat_text)
            try:
                count = int(digits) if digits else 0
            except ValueError:
                count = 0

            org_lower = org_text.lower()
            if (
                "south central railway" in org_lower
                or org_text.strip().upper() == "SCR"
                or org_lower == "south central"
            ):
                scr_row_idx = idx
                scr_count = count
            if org_lower == "total" or org_lower.startswith("total"):
                total_row_idx = idx
                total_count = count

        # Fallback: if Zone is SCR-filtered and no Total/SCR row, sum division Unsatisfactory
        if scr_row_idx is None and total_row_idx is None and row_count > start:
            summed = 0
            last_data_idx = None
            for idx in range(start, row_count):
                row = rows.nth(idx)
                cells = row.locator("td")
                if await cells.count() <= unsat_idx:
                    continue
                org_text = (await cells.nth(org_idx).inner_text()).strip().lower()
                if not org_text or org_text == "total":
                    continue
                unsat_text = (await cells.nth(unsat_idx).inner_text()).strip()
                digits = re.sub(r"[^\d]", "", unsat_text)
                if not digits:
                    continue
                try:
                    summed += int(digits)
                    last_data_idx = idx
                except ValueError:
                    continue
            if summed > 0:
                # Prefer clicking Total if present as a linkable cell elsewhere;
                # otherwise click first row with a link in Unsatisfactory column.
                for idx in range(start, row_count):
                    row = rows.nth(idx)
                    cells = row.locator("td")
                    if await cells.count() <= unsat_idx:
                        continue
                    link = cells.nth(unsat_idx).locator("a")
                    if await link.count() > 0:
                        return summed, idx
                return summed, last_data_idx

        if scr_row_idx is not None and scr_count > 0:
            return scr_count, scr_row_idx
        if total_row_idx is not None and total_count > 0:
            return total_count, total_row_idx
        return 0, None

    async def _click_unsatisfactory_row(
        self, page: "Page", table, row_idx: int
    ) -> bool:
        headers = await self._extract_table_headers(table)
        unsat_idx = self._column_index(headers, "Unsatisfactory")
        if unsat_idx is None:
            unsat_idx = 6

        # Use same row set as _get_scr_unsatisfactory_target (tbody + tfoot)
        rows = table.locator("tbody tr, tfoot tr")
        if await rows.count() == 0:
            rows = table.locator("tr")
        row = rows.nth(row_idx)
        cells = row.locator("td")
        if await cells.count() <= unsat_idx:
            return False

        # Prefer explicit UNSAT drill link when present
        unsat_link = row.locator("a.drill[id*='UNSAT'], a[id*='UNSAT']")
        if await unsat_link.count() > 0:
            await unsat_link.first.click()
        else:
            unsat_cell = cells.nth(unsat_idx)
            link = unsat_cell.locator("a")
            if await link.count() > 0:
                await link.first.click()
            else:
                await unsat_cell.click()

        try:
            await page.wait_for_selector(
                ".modal.show, .modal.fade.show, #exampleModal.show",
                timeout=20000,
            )
            # Wait for modal data rows (DataTables loads async)
            await page.wait_for_selector(
                "#exampleModal table tbody tr td, .modal.show table tbody tr td",
                timeout=20000,
            )
            return True
        except Exception:
            return False

    async def _click_unsatisfactory(self, page: "Page", table) -> bool:
        _, row_idx = await self._get_scr_unsatisfactory_target(table)
        if row_idx is None:
            return False
        return await self._click_unsatisfactory_row(page, table, row_idx)

    async def _extract_modal_pages(self, page: "Page") -> list[dict[str, str]]:
        all_complaints: list[dict[str, str]] = []
        seen_refs: set[str] = set()

        while True:
            await page.wait_for_timeout(500)
            modal_table = page.locator(
                ".modal table, [role='dialog'] table, #complaintListModal table"
            ).first

            if await modal_table.count() == 0:
                break

            headers = await self._extract_table_headers(modal_table)
            rows = modal_table.locator("tbody tr")
            row_count = await rows.count()

            if row_count == 0:
                break

            for row_idx in range(row_count):
                row = rows.nth(row_idx)
                cells = row.locator("td")
                cell_count = await cells.count()
                if cell_count < 3:
                    continue

                row_data: dict[str, str] = {}
                for col_idx in range(min(cell_count, len(headers))):
                    header = headers[col_idx] if col_idx < len(headers) else f"Col{col_idx}"
                    row_data[header] = (await cells.nth(col_idx).inner_text()).strip()

                ref_no = row_data.get("Ref. No.", "")
                if ref_no and ref_no not in seen_refs:
                    seen_refs.add(ref_no)
                    all_complaints.append(row_data)

            next_button = page.locator(
                ".pagination .next:not(.disabled), "
                "button:has-text('Next'):not([disabled]), "
                "a:has-text('Next'):not(.disabled), "
                ".dataTables_paginate .next:not(.disabled)"
            )
            if await next_button.count() > 0 and await next_button.first.is_visible():
                await next_button.first.click()
                await page.wait_for_timeout(1000)
            else:
                break

        return all_complaints

    async def _close_modal(self, page: "Page") -> None:
        close_buttons = page.locator(
            ".modal .close, [role='dialog'] button[aria-label='Close'], "
            ".modal button:has-text('Close'), .modal .btn-close"
        )
        if await close_buttons.count() > 0:
            await close_buttons.first.click()
            await page.wait_for_timeout(500)

    def _save_complaints_csv(
        self,
        complaints: list[dict[str, str]],
        report_slug: str,
    ) -> Path:
        extracted_dir = ensure_directory(resolve_report_dir(config.extracted_data_dir, report_slug))
        csv_path = extracted_dir / f"{report_slug}_complaints_raw.csv"

        if not complaints:
            csv_path.write_text("Ref. No.,Mode\n", encoding="utf-8")
            return csv_path

        all_keys: set[str] = set()
        for complaint in complaints:
            all_keys.update(complaint.keys())
        headers = ["Ref. No.", "Mode"] + sorted(all_keys - {"Ref. No.", "Mode"})

        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(complaints)

        return csv_path
