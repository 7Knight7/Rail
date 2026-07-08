"""Report generation (view/load) without download for in-process automation."""

from __future__ import annotations

import logging
from pathlib import Path

from playwright.async_api import FrameLocator, Page, TimeoutError as PlaywrightTimeoutError

from app.automation.config import config
from app.automation.filters import ReportRoot
from app.automation.selectors import selectors
from app.automation.utils import ensure_directory, log_automation_event
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

PHASE5_BEFORE_SCREENSHOT = "phase5_before_generate.png"
PHASE5_AFTER_SCREENSHOT = "phase5_report_loaded.png"

EXPORT_KEYWORDS = ("export", "download", "excel", "pdf", "xlsx")
GENERATE_BUTTON_TEXTS = (
    "Submit",
    "Generate",
    "View Report",
    "Show Report",
    "Search",
    "View",
)
LOADING_SELECTORS = (
    ".loading",
    ".loader",
    "[class*='loading']",
    "[class*='spinner']",
    "[class*='Loader']",
    "#loading",
    "#loader",
)


class ReportGenerationError(AppException):
    """Raised when report generation or results verification fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="REPORT_GENERATION_ERROR")


class ReportGeneratorService:
    """Clicks generate/view and verifies the report grid is visible."""

    async def capture_before_generate(self, page: Page) -> str:
        path = await self._capture(page, PHASE5_BEFORE_SCREENSHOT)
        log_automation_event(logger, "report_before_generate_screenshot", path=path)
        return path

    async def capture_report_loaded(self, page: Page) -> str:
        path = await self._capture(page, PHASE5_AFTER_SCREENSHOT)
        log_automation_event(logger, "report_screenshot_saved", path=path, stage="report_loaded")
        return path

    async def _capture(self, page: Page, filename: str) -> str:
        directory = ensure_directory(Path(config.debug_screenshots_dir))
        path = directory / filename
        await page.screenshot(path=str(path), full_page=True)
        return str(path)

    async def generate_report(self, root: ReportRoot, page: Page) -> None:
        """Click the generate/submit button and wait for the report to load."""
        button = await self._find_generate_button(root)
        if button is None:
            raise ReportGenerationError("Generate/View Report button not found")

        button_text = await self._button_label(button)
        log_automation_event(logger, "report_generate_click", button_text=button_text)
        await button.click()

        await self._wait_for_report_loaded(root, page)

    async def _wait_for_report_loaded(self, root: ReportRoot, page: Page) -> None:
        timeout_ms = min(config.timeout * 1000, 90_000)

        try:
            await page.wait_for_load_state("networkidle", timeout=timeout_ms)
        except PlaywrightTimeoutError:
            logger.warning("networkidle timeout after generate click; continuing")

        await self._wait_for_loading_indicators(root, timeout_ms)

        table = root.locator(selectors.report1_table).first
        grid = root.locator(selectors.report1_grid).first

        table_visible = False
        for target in (table, grid):
            if await target.count() == 0:
                continue
            try:
                await target.wait_for(state="visible", timeout=timeout_ms)
                table_visible = True
                break
            except PlaywrightTimeoutError:
                continue

        if not table_visible:
            rows = root.locator(f"{selectors.report1_table} tbody tr, {selectors.report1_grid} tr")
            if await rows.count() > 0:
                table_visible = True

        if not table_visible:
            raise ReportGenerationError(
                "Report table/grid did not become visible after generate"
            )

    async def _wait_for_loading_indicators(self, root: ReportRoot, timeout_ms: int) -> None:
        for selector in LOADING_SELECTORS:
            loader = root.locator(selector)
            if await loader.count() == 0:
                continue
            try:
                await loader.first.wait_for(state="hidden", timeout=min(timeout_ms, 30_000))
            except PlaywrightTimeoutError:
                logger.debug("Loader still visible for selector %s", selector)

    async def _find_generate_button(self, root: ReportRoot):
        candidates = [
            root.locator(selectors.report1_generate),
        ]
        for text in GENERATE_BUTTON_TEXTS:
            candidates.extend(
                [
                    root.locator(f"input[type='submit'][value*='{text}']"),
                    root.locator(f"button:has-text('{text}')"),
                    root.locator(f"input[value*='{text}']"),
                    root.locator(f"a:has-text('{text}')"),
                ]
            )
        candidates.extend(
            [
                root.locator("input[type='submit']"),
                root.locator("button[type='submit']"),
            ]
        )

        for locator in candidates:
            count = await locator.count()
            for index in range(count):
                candidate = locator.nth(index)
                if not await candidate.is_visible():
                    continue
                if await self._is_export_button(candidate):
                    continue
                return candidate
        return None

    async def _button_label(self, locator) -> str:
        try:
            text = (await locator.inner_text()).strip()
            if text:
                return text
        except Exception:
            pass
        try:
            return (await locator.get_attribute("value") or "").strip()
        except Exception:
            return ""

    async def _is_export_button(self, locator) -> bool:
        label = (await self._button_label(locator)).lower()
        combined = label
        try:
            combined = f"{label} {(await locator.get_attribute('value') or '').lower()}"
        except Exception:
            pass
        return any(keyword in combined for keyword in EXPORT_KEYWORDS)

    async def count_rows(self, root: ReportRoot) -> int:
        """Best-effort count of rows in the report results table."""
        table = root.locator(selectors.report1_table).first
        if await table.count() == 0:
            table = root.locator(selectors.report1_grid).first
        if await table.count() == 0:
            return 0
        rows = root.locator(f"{selectors.report1_table} tbody tr, {selectors.report1_grid} tbody tr")
        if await rows.count() == 0:
            rows = root.locator(f"{selectors.report1_table} tr, {selectors.report1_grid} tr")
        return await rows.count()

    async def verify_report_displayed(self, root: ReportRoot) -> bool:
        table = root.locator(selectors.report1_table).first
        grid = root.locator(selectors.report1_grid).first
        for target in (table, grid):
            if await target.count() == 0:
                continue
            if await target.is_visible():
                return True
        return await self.count_rows(root) > 0

    async def log_report_metadata(self, page: Page, row_count: int) -> None:
        try:
            page_title = await page.title()
        except Exception:
            page_title = ""
        log_automation_event(
            logger,
            "report_generated",
            page_url=page.url,
            page_title=page_title,
            row_count=row_count,
        )
