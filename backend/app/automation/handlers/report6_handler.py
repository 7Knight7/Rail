"""Report 6 / scr-station handler: SCR Station Mode Unsatisfactory modal extraction."""

from __future__ import annotations

import logging
import re
import time
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from app.automation.config import config
from app.automation.report1_filters import FilterFieldDefinition
from app.automation.report6_scr_filters import REPORT_6_SCR_FILTERS
from app.automation.reports import ReportDefinition
from app.automation.schemas import ReportResult
from app.automation.utils import ensure_directory, log_automation_event

from .report5_handler import Report5Handler

if TYPE_CHECKING:
    from playwright.async_api import Page

    from app.automation.session import SessionManager

logger = logging.getLogger(__name__)

SCR_STATION_UNSATISFACTORY_NOT_FOUND = "SCR_STATION_UNSATISFACTORY_NOT_FOUND"

ZONE_WISE_REQUIRED_HEADERS = (
    "organisation",
    "feedback received",
    "% feedback",
    "excellent",
    "satisfactory",
    "unsatisfactory",
    "% unsatisfactory",
)


class _TargetStatus(str, Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"


class Report6Handler(Report5Handler):
    """Execute SCR Station Unsatisfactory workflow (canonical key: scr-station)."""

    expected_mode = "Station"

    async def execute(
        self,
        page: "Page",
        session: "SessionManager",
        report: ReportDefinition,
    ) -> ReportResult:
        started_at = datetime.now(UTC).isoformat()
        t0 = time.perf_counter()
        page = await self.ensure_mis_page(page, session, f"{report.slug}_start")

        report_root = await self._apply_station_filters(page, session, report, full=False)

        await self.click_received_twice(
            report_root, page, feedback=True, report_slug=report.slug
        )

        expected_count, complaints, error = await self._extract_scr_complaints(
            page, report_root, report.slug
        )

        if error == SCR_STATION_UNSATISFACTORY_NOT_FOUND:
            log_automation_event(
                logger,
                "scr_station_unsatisfactory_retry",
                slug=report.slug,
                reason="not_found_first_pass",
            )
            page = await self.ensure_mis_page(page, session, f"{report.slug}_retry")
            report_root = await self._apply_station_filters(
                page, session, report, full=True
            )
            await self.click_received_twice(
                report_root, page, feedback=True, report_slug=report.slug
            )
            expected_count, complaints, error = await self._extract_scr_complaints(
                page, report_root, report.slug
            )
            if error == SCR_STATION_UNSATISFACTORY_NOT_FOUND:
                await self._save_not_found_artifacts(page, session, report.slug)
                return self.build_failed_result(report.slug, SCR_STATION_UNSATISFACTORY_NOT_FOUND)

        page = await self.ensure_mis_page(page, session, f"{report.slug}_after_modal")

        if error:
            return self.build_failed_result(report.slug, error)

        if expected_count == 0:
            log_automation_event(
                logger,
                "no_station_unsatisfactory_complaints",
                slug=report.slug,
                expected_count=0,
            )

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

        await self.archive_pdf(page, report_root, report.slug, session=session)

        extraction_seconds = time.perf_counter() - t0
        log_automation_event(
            logger,
            "report_extraction_completed",
            slug=report.slug,
            extracted_count=len(complaints),
            expected_count=expected_count,
            duration_seconds=round(extraction_seconds, 3),
        )
        return await self.finalize_after_extract(
            slug=report.slug,
            csv_path=csv_path,
            source_paths=source_paths,
            row_counts=row_counts,
            source_row_count=len(complaints),
            ingest_source="scr_modal_csv",
            started_at=started_at,
            extraction_seconds=round(extraction_seconds, 3),
        )

    async def _apply_station_filters(
        self,
        page: "Page",
        session: "SessionManager",
        report: ReportDefinition,
        *,
        full: bool,
    ):
        """Apply Mode-only switch when already on Tab 6, else full Station filters.

        When ``full=True`` (retry), always re-apply the complete Station filter set.
        """
        already_on_feedback = "mis_reports/report6" in page.url
        if already_on_feedback and not full:
            log_automation_event(
                logger,
                "report_navigate_skip",
                report=report.slug,
                reason="reuse_tab6_mode_switch",
            )
            mode_only = [
                FilterFieldDefinition(
                    name="mode",
                    selector="#complaintModeInput",
                    field_type="select",
                    value="Station",
                    required=True,
                    label="Mode",
                )
            ]
            report_root, _, _ = await self.apply_filters_and_submit(
                page, report, filters=mode_only, session=session
            )
            return report_root

        if not already_on_feedback:
            await self.navigation.navigate_to_report(page, report)
            page = await self.ensure_mis_page(page, session, f"{report.slug}_after_nav")

        report_root, _, _ = await self.apply_filters_and_submit(
            page, report, filters=REPORT_6_SCR_FILTERS, session=session
        )
        return report_root

    async def _save_not_found_artifacts(
        self,
        page: "Page",
        session: "SessionManager",
        report_slug: str,
    ) -> None:
        dest = ensure_directory(Path(config.screenshots_dir))
        try:
            await session.capture_screenshot(page, dest)
        except Exception as exc:
            logger.warning("scr-station not-found screenshot failed: %s", exc)
        try:
            html = await page.content()
            stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            html_path = dest / f"failure_{stamp}_{report_slug}_unsatisfactory_not_found.html"
            html_path.write_text(html, encoding="utf-8")
            log_automation_event(
                logger,
                "scr_station_not_found_html_saved",
                path=str(html_path),
            )
        except Exception as exc:
            logger.warning("scr-station not-found HTML save failed: %s", exc)

    @staticmethod
    def _is_zone_wise_table(headers: list[str]) -> bool:
        """Require the Zone Wise feedback header set (skip wrong tables)."""
        lower = [h.strip().lower() for h in headers]
        has_org = any(h in {"organisation", "organization"} or "organisation" in h or "organization" in h for h in lower)
        has_feedback = any("feedback received" in h for h in lower)
        has_pct_feedback = any("% feedback" in h for h in lower)
        has_excellent = any(h == "excellent" or h.startswith("excellent") for h in lower)
        has_satisfactory = any(h == "satisfactory" for h in lower)
        has_unsat = any(h == "unsatisfactory" for h in lower)
        has_pct_unsat = any(h == "% unsatisfactory" or (h.startswith("%") and "unsatisfactory" in h) for h in lower)
        return (
            has_org
            and has_feedback
            and has_pct_feedback
            and has_excellent
            and has_satisfactory
            and has_unsat
            and has_pct_unsat
        )

    @staticmethod
    def _exact_column_index(headers: list[str], name: str) -> int | None:
        """Exact header match (case-insensitive); never substring (% Unsatisfactory)."""
        target = name.strip().lower()
        for idx, header in enumerate(headers):
            if header.strip().lower() == target:
                return idx
        return None

    async def _get_station_unsatisfactory_target(
        self, table
    ) -> tuple[_TargetStatus, int, int | None]:
        """Return (status, count, row_index) for Total/SCR Unsatisfactory cell.

        Blank or \"0\" parse as zero only when the correct cell exists.
        """
        headers = await self._extract_table_headers(table)
        org_idx = self._exact_column_index(headers, "Organisation")
        if org_idx is None:
            org_idx = self._exact_column_index(headers, "Organization")
        unsat_idx = self._exact_column_index(headers, "Unsatisfactory")
        if org_idx is None or unsat_idx is None:
            return _TargetStatus.NOT_FOUND, 0, None

        rows = table.locator("tbody tr, tfoot tr")
        row_count = await rows.count()
        if row_count == 0:
            rows = table.locator("tr")
            row_count = await rows.count()

        total_row_idx: int | None = None
        total_count = 0
        total_found = False
        scr_row_idx: int | None = None
        scr_count = 0
        scr_found = False

        start = 0
        if row_count > 0:
            first_cells = rows.nth(0).locator("th, td")
            if await first_cells.count() > 0:
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
                scr_found = True
            if org_lower == "total" or org_lower.startswith("total"):
                total_row_idx = idx
                total_count = count
                total_found = True

        # Prefer Total row (zone already filtered to SCR); else SCR organisation row.
        if total_found and total_row_idx is not None:
            return _TargetStatus.FOUND, total_count, total_row_idx
        if scr_found and scr_row_idx is not None:
            return _TargetStatus.FOUND, scr_count, scr_row_idx
        return _TargetStatus.NOT_FOUND, 0, None

    async def _extract_scr_complaints(
        self,
        page: "Page",
        report_root,
        report_slug: str,
    ) -> tuple[int, list[dict[str, str]], str | None]:
        table = await self._find_zone_wise_table(report_root)
        if table is None:
            return 0, [], SCR_STATION_UNSATISFACTORY_NOT_FOUND

        status, expected_count, target_row_idx = await self._get_station_unsatisfactory_target(
            table
        )
        if status == _TargetStatus.NOT_FOUND or target_row_idx is None:
            return 0, [], SCR_STATION_UNSATISFACTORY_NOT_FOUND

        # Count found and value is 0 (or blank parsed as 0): valid empty success.
        if expected_count == 0:
            return 0, [], None

        if not await self._click_unsatisfactory_row_exact(page, table, target_row_idx):
            return expected_count, [], "Failed to open complaints modal"

        complaints = await self._extract_modal_pages(page)
        await self._close_modal(page)

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

    async def _click_unsatisfactory_row_exact(
        self, page: "Page", table, row_idx: int
    ) -> bool:
        """Click Total-row Unsatisfactory using exact column header match."""
        headers = await self._extract_table_headers(table)
        unsat_idx = self._exact_column_index(headers, "Unsatisfactory")
        if unsat_idx is None:
            return False

        rows = table.locator("tbody tr, tfoot tr")
        if await rows.count() == 0:
            rows = table.locator("tr")
        row = rows.nth(row_idx)
        cells = row.locator("td")
        if await cells.count() <= unsat_idx:
            return False

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
            await page.wait_for_selector(
                "#exampleModal table tbody tr td, .modal.show table tbody tr td",
                timeout=20000,
            )
            return True
        except Exception:
            return False
