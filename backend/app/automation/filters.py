"""Report filter discovery and application for in-process Playwright automation."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from playwright.async_api import FrameLocator, Locator, Page, TimeoutError as PlaywrightTimeoutError

from app.automation.config import config
from app.automation.report1_filters import (
    FilterFieldDefinition,
    normalize_discovered_field,
    resolve_field_value,
)
from app.automation.selectors import selectors
from app.automation.utils import ensure_directory, log_automation_event
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

ReportRoot = Page | FrameLocator

DISCOVERY_SCRIPT = """
() => {
  const results = [];
  const seen = new Set();
  const elements = document.querySelectorAll('input, select, textarea, button');
  for (const el of elements) {
    const tag = el.tagName.toLowerCase();
    const field_id = el.id || '';
    const field_name = el.name || '';
    const field_type = el.type || tag;
    const placeholder = el.placeholder || '';
    let field_label = '';
    if (field_id) {
      const labelEl = document.querySelector(`label[for="${field_id}"]`);
      if (labelEl) field_label = (labelEl.textContent || '').trim();
    }
    if (!field_label && el.closest('label')) {
      field_label = (el.closest('label').textContent || '').trim();
    }
    if (!field_label) {
      const row = el.closest('tr');
      if (row) {
        const cells = row.querySelectorAll('td, th');
        for (const cell of cells) {
          if (cell.contains(el)) continue;
          const text = (cell.textContent || '').trim();
          if (text) {
            field_label = text;
            break;
          }
        }
      }
    }
    const options = tag === 'select'
      ? Array.from(el.options).map(o => ({
          value: o.value,
          label: (o.textContent || '').trim(),
        }))
      : [];
    const selector = field_id
      ? `#${field_id}`
      : (field_name ? `[name="${field_name}"]` : tag);
    const key = `${tag}:${field_id}:${field_name}:${selector}`;
    if (seen.has(key)) continue;
    seen.add(key);
    let current_value = el.value || '';
    if (tag === 'select' && el.selectedIndex >= 0) {
      current_value = (el.options[el.selectedIndex]?.textContent || '').trim();
    }
    results.push({
      tag,
      field_id,
      field_name,
      field_type,
      placeholder,
      field_label,
      required: el.required || false,
      current_value,
      options,
      selector,
    });
  }
  return results;
}
"""


class FilterError(AppException):
    """Raised when filter discovery, application, or validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="FILTER_ERROR")


class FilterDiscoveryService:
    """Discovers form fields inside the Report 1 page or iframe."""

    async def discover_fields(self, page: Page) -> list[dict[str, Any]]:
        """Scan the report surface and persist discovered field metadata."""
        root = await FilterService.get_report_root(page)
        raw_fields: list[dict[str, Any]] = await root.locator("body").first.evaluate(
            DISCOVERY_SCRIPT
        )
        fields = [normalize_discovered_field(field) for field in raw_fields]

        for field in fields:
            log_automation_event(
                logger,
                "filter_field_discovered",
                field_name=field.get("field_name") or field.get("field_id") or field.get("tag"),
                field_id=field.get("field_id"),
                field_type=field.get("field_type"),
                selector=field.get("selector"),
                field_label=field.get("field_label"),
                field_value=field.get("current_value"),
            )

        output_path = Path(config.debug_screenshots_dir) / "report1_fields.json"
        ensure_directory(output_path.parent)
        output_path.write_text(json.dumps(fields, indent=2), encoding="utf-8")
        log_automation_event(
            logger,
            "filter_discovery_saved",
            path=str(output_path),
            count=len(fields),
        )
        return fields


class FilterService:
    """Applies configured filters to the Report 1 form."""

    @staticmethod
    async def get_report_root(page: Page) -> ReportRoot:
        """Return the page or iframe containing the report filter form."""
        try:
            await page.wait_for_selector(
                "select, input, textarea, iframe",
                timeout=10_000,
            )
        except PlaywrightTimeoutError:
            logger.warning("Timed out waiting for report form controls")

        iframe_count = await page.locator("iframe").count()
        for index in range(iframe_count):
            frame_loc = page.frame_locator("iframe").nth(index)
            if await frame_loc.locator("input, select, textarea").count() > 0:
                log_automation_event(
                    logger,
                    "report_context_resolved",
                    location="iframe",
                    frame_index=index,
                )
                return frame_loc

        for frame_selector in selectors.report1_frame.split(","):
            frame_selector = frame_selector.strip()
            if not frame_selector:
                continue
            frame_loc = page.frame_locator(frame_selector).first
            if await frame_loc.locator("input, select, textarea").count() > 0:
                log_automation_event(
                    logger,
                    "report_context_resolved",
                    location="iframe",
                    frame_selector=frame_selector,
                )
                return frame_loc

        if await page.locator("select, input, textarea").count() > 0:
            log_automation_event(logger, "report_context_resolved", location="main_page")
            return page

        raise FilterError("Report form not found on the page (no iframe or main-page controls)")

    @staticmethod
    async def get_report_frame(page: Page) -> ReportRoot:
        """Backward-compatible alias for get_report_root."""
        return await FilterService.get_report_root(page)

    async def apply_filters(
        self,
        root: ReportRoot,
        fields: list[FilterFieldDefinition],
        page: Page | None = None,
    ) -> dict[str, str]:
        """Populate all configured filters and return applied name/value pairs."""
        applied: dict[str, str] = {}
        date_format = config.date_format

        for field in fields:
            locator = await self._resolve_field_locator(root, field)
            if await locator.count() == 0:
                if field.required:
                    raise FilterError(
                        f"Required filter field not found: {field.name} ({field.selector})"
                    )
                logger.warning("Optional filter field not found: %s", field.name)
                continue

            value = resolve_field_value(field, date_format=date_format)
            applied_value = await self._apply_field(locator, field, value)
            applied[field.name] = applied_value
            log_automation_event(
                logger,
                "filter_field_set",
                field_name=field.name,
                field_value=applied_value,
                field_label=field.label or field.name,
            )
            await asyncio.sleep(config.filter_interaction_delay_ms / 1000)
            if field.field_type == "select" and page is not None:
                await self._wait_for_dependent_controls(page)

        return applied

    @staticmethod
    async def _wait_for_dependent_controls(page: Page) -> None:
        try:
            await page.wait_for_load_state("networkidle", timeout=5_000)
        except PlaywrightTimeoutError:
            logger.debug("networkidle wait skipped after filter change")

    async def _resolve_field_locator(
        self,
        root: ReportRoot,
        field: FilterFieldDefinition,
    ) -> Locator:
        locator = root.locator(field.selector).first
        if await locator.count() > 0:
            return locator

        if field.label:
            label_locator = root.locator(
                f"tr:has(td:text-is('{field.label}')) select, "
                f"tr:has(td:text-is('{field.label}')) input, "
                f"tr:has(th:text-is('{field.label}')) select, "
                f"tr:has(th:text-is('{field.label}')) input, "
                f"td:text-is('{field.label}') + td select, "
                f"td:text-is('{field.label}') + td input, "
                f"label:text-is('{field.label}') + select, "
                f"label:text-is('{field.label}') + input, "
                f"tr:has(td:has-text('{field.label}')) select, "
                f"tr:has(th:has-text('{field.label}')) select, "
                f"td:has-text('{field.label}') + td select, "
                f"label:has-text('{field.label}') + select"
            ).first
            if await label_locator.count() > 0:
                return label_locator

        return locator

    async def _apply_field(
        self,
        locator: Locator,
        field: FilterFieldDefinition,
        value: str,
    ) -> str:
        if field.field_type == "select":
            return await self._apply_select(locator, value)
        if field.field_type == "checkbox":
            await self._apply_checkbox(locator, value)
            return value
        if field.field_type == "radio":
            await self._apply_radio(locator, value)
            return value
        await self._apply_text_or_date(locator, value)
        return value

    async def _apply_text_or_date(self, locator: Locator, value: str) -> None:
        if not await locator.is_visible():
            await locator.evaluate(
                """(el, value) => {
                    el.value = value;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }""",
                value,
            )
            return
        try:
            await locator.fill(value)
        except Exception:
            await locator.click()
            await locator.fill(value)
            await locator.press("Enter")

    async def _apply_select(self, locator: Locator, value: str) -> str:
        candidates = [value]
        normalized = value.lower().strip()
        if normalized in {"previous day", "prev_day", "previous_day", "today_range", "previous_day_range"}:
            candidates.extend(
                [
                    "Previous Day",
                    "PREV_DAY",
                    "PREVIOUS DAY",
                    "PreviousDay",
                ]
            )
        elif normalized == "today":
            candidates.extend(["Today", "Current Day", "CURRENT DAY", "TODAY"])
        for candidate in candidates:
            try:
                await locator.select_option(label=candidate)
                return candidate
            except Exception:
                try:
                    await locator.select_option(value=candidate)
                    return candidate
                except Exception:
                    continue
        selected = await locator.evaluate(
            "el => el.options[el.selectedIndex]?.text ?? ''"
        )
        if selected:
            return str(selected)
        raise FilterError(f"Could not select option '{value}' for dropdown")

    async def _apply_checkbox(self, locator: Locator, value: str) -> None:
        should_check = value.lower() in {"true", "1", "yes", "on", "checked"}
        if should_check and not await locator.is_checked():
            await locator.check()

    async def _apply_radio(self, locator: Locator, value: str) -> None:
        target = locator
        if await locator.count() > 1:
            target = locator.filter(has_text=value).first
            if await target.count() == 0:
                target = locator.locator(f"[value='{value}']").first
        if await target.count() > 0 and not await target.is_checked():
            await target.check()

    async def validate_mandatory(
        self,
        root: ReportRoot,
        fields: list[FilterFieldDefinition],
        applied: dict[str, str],
    ) -> None:
        """Ensure every required filter has a non-empty value."""
        missing: list[str] = []
        for field in fields:
            if not field.required:
                continue
            locator = await self._resolve_field_locator(root, field)
            if await locator.count() == 0:
                missing.append(f"{field.name} (not found)")
                continue
            current = applied.get(field.name, "")
            if not str(current).strip():
                current = await self._read_field_value(locator, field.field_type)
            if not str(current).strip():
                missing.append(field.name)

        if missing:
            raise FilterError(f"Mandatory filters missing or empty: {', '.join(missing)}")

        log_automation_event(logger, "filters_validated", count=len(applied))

    @staticmethod
    async def _read_field_value(locator: Locator, field_type: str) -> str:
        if field_type == "select":
            return str(
                await locator.evaluate("el => el.options[el.selectedIndex]?.text ?? ''")
            )
        try:
            return await locator.input_value()
        except Exception:
            return ""
