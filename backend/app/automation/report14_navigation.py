"""Report 14 portal navigation via MIS Reports sidebar (not URL-only).

Report 14 always opens portal menu item **11) Train Watering Complaint** only.
Do not click Inquiry Wise 2 (tab 14), direct report11 URLs, or other MIS tabs —
a blank shell is left when only ?page=/mis_reports/report11 is opened.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from playwright.async_api import FrameLocator, Page, TimeoutError as PlaywrightTimeoutError

from app.automation.config import config
from app.automation.utils import ensure_directory, log_automation_event
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

MIS_REPORTS_LABEL = "MIS Reports"
TAB11_MENU_LABEL = "11) Train Watering Complaint"
# Wrapped sidebar text may split across lines; normalized match still finds it.
TAB11_MENU_PATTERN = re.compile(
    r"^11\)\s*Train\s*Watering\s*Complaint$",
    re.IGNORECASE,
)
# Reject multi-row sidebar blobs / wrong numbered tabs.
_TAB11_MAX_LABEL_LEN = 48

FORM_HEADING_MARKERS = (
    "Train Watering Wise Report",
    "Train Watering Wise",
    "Train Watering Complaint",
    "Watering Wise Report",
)

# Watering-specific markers so other MIS forms (Inquiry Wise, Comprehensive, …)
# are never treated as Report 14 success.
WATERING_OUTPUT_MARKERS = (
    "Previous Watering Point",
    "Upcoming Watering Point",
)

# Controls on the Train Watering form (used only with a watering heading).
FORM_CONTROL_LABELS = (
    "From Date",
    "To Date",
    "Zone",
    "Division",
    "Sub Type",
    "Department",
    "View",
    "Coach Type",
    "Output",
    "Submit",
)

NAV_STAGE = "report14_tab11_navigation"
NAV_ERROR_MESSAGE = (
    "Report 14 failed: Train Watering Complaint form did not load after selecting "
    "MIS Reports → 11) Train Watering Complaint."
)


class Report14NavigationError(AppException):
    """Raised when Report 14 tab-11 navigation/form load fails."""

    def __init__(self, message: str = NAV_ERROR_MESSAGE, *, stage: str = NAV_STAGE) -> None:
        super().__init__(message=message, code="REPORT14_NAVIGATION_FAILED")
        self.stage = stage


def normalize_menu_text(text: str) -> str:
    """Collapse whitespace so wrapped menu labels match a single target string."""
    return re.sub(r"\s+", " ", (text or "").replace("\xa0", " ").strip())


def menu_text_matches_tab11(text: str) -> bool:
    """True only for the leaf sidebar row 11) Train Watering Complaint.

    Rejects parent containers that include other tabs and never matches
    14) Inquiry Wise 2 or other numbered MIS items.
    """
    compact = normalize_menu_text(text)
    if not compact:
        return False
    if len(compact) > _TAB11_MAX_LABEL_LEN:
        return False
    # Multi-item blobs include neighboring numbers.
    if re.search(r"(?<!\d)(?:10|12|13|14|15)\)", compact):
        return False
    if normalize_menu_text(TAB11_MENU_LABEL).lower() == compact.lower():
        return True
    return bool(TAB11_MENU_PATTERN.match(compact))


async def _locator_visible_count(locator: Any) -> int:
    try:
        return await locator.count()
    except Exception:
        return 0


async def _save_nav_diagnostics(
    page: Page,
    *,
    run_id: str,
    reason: str,
    mis_expanded: bool | None = None,
    tab11_clicked: bool | None = None,
) -> None:
    dest = ensure_directory(Path(config.debug_screenshots_dir) / "report14_nav")
    stem = f"report14_nav_{run_id[:8]}_{reason}"
    try:
        await page.screenshot(path=str(dest / f"{stem}.png"), full_page=True)
    except Exception as exc:
        logger.warning("report14 nav screenshot failed: %s", exc)
    try:
        html = await page.content()
        (dest / f"{stem}.html").write_text(html[:500_000], encoding="utf-8")
    except Exception as exc:
        logger.warning("report14 nav html dump failed: %s", exc)

    frames = []
    try:
        for fr in page.frames:
            frames.append({"url": fr.url, "name": fr.name})
    except Exception:
        pass

    log_automation_event(
        logger,
        "report14_navigation_failed",
        stage=NAV_STAGE,
        reason=reason,
        url=page.url,
        mis_expanded=mis_expanded,
        tab11_clicked=tab11_clicked,
        frames=frames,
        diagnostic_dir=str(dest),
    )


async def _find_mis_reports_control(page: Page) -> Any:
    """Locate the left-rail MIS Reports menu item by exact visible text."""
    # Prefer exact text on interactive ancestors (buttons / menu rows).
    candidates = [
        page.get_by_role("button", name=MIS_REPORTS_LABEL, exact=True),
        page.get_by_role("link", name=MIS_REPORTS_LABEL, exact=True),
        page.get_by_text(MIS_REPORTS_LABEL, exact=True),
        page.locator(f"text={MIS_REPORTS_LABEL}"),
    ]
    for loc in candidates:
        try:
            first = loc.first
            if await first.count() > 0 and await first.is_visible():
                return first
        except Exception:
            continue
    # Fuzzy: any element whose normalized text is exactly MIS Reports
    all_mis = page.locator("body *").filter(has_text=re.compile(r"^\s*MIS\s*Reports\s*$", re.I))
    if await all_mis.count() > 0:
        return all_mis.first
    return None


async def _is_tab11_visible(page: Page) -> bool:
    loc = await _find_tab11_control(page)
    if loc is None:
        return False
    try:
        return await loc.is_visible()
    except Exception:
        return False


async def _find_tab11_control(page: Page) -> Any:
    """Locate only 11) Train Watering Complaint (leaf row; handles wrapped text)."""
    # Exact single-line first
    for ctor in (
        lambda: page.get_by_role("link", name=TAB11_MENU_LABEL, exact=True),
        lambda: page.get_by_role("button", name=TAB11_MENU_LABEL, exact=True),
        lambda: page.get_by_role("menuitem", name=TAB11_MENU_LABEL, exact=True),
        lambda: page.get_by_text(TAB11_MENU_LABEL, exact=True),
    ):
        try:
            loc = ctor().first
            if await loc.count() > 0 and await loc.is_visible():
                return loc
        except Exception:
            continue

    # Pattern match on leaf text nodes (handles wrapping / double spaces).
    # Prefer the shortest matching locator later if scan is needed.
    pattern_loc = page.get_by_text(re.compile(r"11\)\s*Train\s*Watering\s*Complaint", re.I))
    try:
        pcount = min(await pattern_loc.count(), 20)
    except Exception:
        pcount = 0
    pattern_hits: list[tuple[int, Any]] = []
    for i in range(pcount):
        item = pattern_loc.nth(i)
        try:
            text = normalize_menu_text(await item.inner_text(timeout=500))
            if not menu_text_matches_tab11(text):
                continue
            if await item.is_visible():
                pattern_hits.append((len(text), item))
        except Exception:
            continue
    if pattern_hits:
        pattern_hits.sort(key=lambda t: t[0])
        return pattern_hits[0][1]

    # Scan candidate menu items; pick shortest leaf match only
    candidates = page.locator(
        "a, button, li, span, div, td, [role='menuitem'], [role='treeitem']"
    )
    try:
        count = min(await candidates.count(), 200)
    except Exception:
        count = 0
    hits: list[tuple[int, Any]] = []
    for i in range(count):
        item = candidates.nth(i)
        try:
            text = normalize_menu_text(await item.inner_text(timeout=500))
        except Exception:
            continue
        if not menu_text_matches_tab11(text):
            continue
        try:
            if not await item.is_visible():
                continue
        except Exception:
            pass
        hits.append((len(text), item))
    if hits:
        hits.sort(key=lambda t: t[0])
        return hits[0][1]
    return None


async def ensure_mis_reports_expanded(page: Page) -> bool:
    """Expand MIS Reports once if needed; return True when submenu is available."""
    if await _is_tab11_visible(page):
        log_automation_event(logger, "report14_mis_already_expanded")
        return True

    control = await _find_mis_reports_control(page)
    if control is None:
        log_automation_event(logger, "report14_mis_reports_not_found")
        return False

    log_automation_event(logger, "report14_mis_reports_click")
    await control.click(timeout=8_000)

    # Wait for submenu: tab 11 becomes visible
    for _ in range(20):
        if await _is_tab11_visible(page):
            log_automation_event(logger, "report14_mis_submenu_expanded")
            return True
        try:
            await page.wait_for_timeout(250)
        except Exception:
            pass

    # Already expanded but click may have collapsed — second attempt if still hidden
    if not await _is_tab11_visible(page):
        control = await _find_mis_reports_control(page)
        if control is not None:
            await control.click(timeout=5_000)
            for _ in range(12):
                if await _is_tab11_visible(page):
                    return True
                await page.wait_for_timeout(250)
    return await _is_tab11_visible(page)


async def click_tab11_train_watering(page: Page) -> bool:
    """Scroll to and click only 11) Train Watering Complaint once."""
    loc = await _find_tab11_control(page)
    if loc is None:
        return False
    try:
        await loc.scroll_into_view_if_needed(timeout=5_000)
    except Exception:
        pass
    log_automation_event(logger, "report14_tab11_click", label=TAB11_MENU_LABEL)
    await loc.click(timeout=8_000)
    return True


async def _text_present(ctx: Page | FrameLocator, text: str) -> bool:
    try:
        if await ctx.get_by_text(text, exact=False).count() > 0:
            return True
    except Exception:
        pass
    try:
        if await ctx.locator(f"text={text}").count() > 0:
            return True
    except Exception:
        pass
    return False


async def _has_watering_heading(ctx: Page | FrameLocator) -> bool:
    for heading in FORM_HEADING_MARKERS:
        if await _text_present(ctx, heading):
            return True
    return False


async def _has_watering_output_marker(ctx: Page | FrameLocator) -> bool:
    for marker in WATERING_OUTPUT_MARKERS:
        if await _text_present(ctx, marker):
            return True
    return False


async def _count_form_signals(ctx: Page | FrameLocator) -> tuple[int, list[str]]:
    """Count label/input signals; does not alone prove Train Watering form."""
    found: list[str] = []
    for label in FORM_CONTROL_LABELS:
        try:
            loc = ctx.locator(
                f"text={label}, label:has-text('{label}'), "
                f"td:has-text('{label}'), th:has-text('{label}'), "
                f"button:has-text('{label}'), input[value='{label}']"
            ).first
            if await loc.count() > 0:
                found.append(label)
        except Exception:
            continue
    for heading in FORM_HEADING_MARKERS:
        if await _text_present(ctx, heading):
            found.append(f"heading:{heading}")
            break
    for marker in WATERING_OUTPUT_MARKERS:
        if await _text_present(ctx, marker):
            found.append(f"output:{marker}")
    for sel in ("#complaintZoneInput", "#fromInput", "#toInput", "select", "form"):
        try:
            if await ctx.locator(sel).count() > 0:
                found.append(f"sel:{sel}")
        except Exception:
            pass
    return len(found), found


async def is_train_watering_form(ctx: Page | FrameLocator) -> tuple[bool, list[str]]:
    """True only when the Train Watering form is present (not other MIS reports)."""
    score, found = await _count_form_signals(ctx)
    has_heading = any(f.startswith("heading:") for f in found) or await _has_watering_heading(
        ctx
    )
    has_output = any(f.startswith("output:") for f in found) or await _has_watering_output_marker(
        ctx
    )
    # Require watering identity + enough shared controls.
    if has_heading and score >= 3:
        return True, found
    if has_heading and has_output:
        return True, found
    if has_output and score >= 4:
        return True, found
    return False, found


async def resolve_report14_form_context(page: Page) -> Page | FrameLocator | None:
    """Return context only when Train Watering form is present (tab 11 content)."""
    try:
        for frame in page.frames:
            if frame == page.main_frame:
                continue
            try:
                fl = None
                if frame.name:
                    fl = page.frame_locator(f"iframe[name='{frame.name}']")
                if fl is None and frame.url:
                    fl = page.frame_locator(
                        "iframe[src*='mis_reports'], iframe[src*='report']"
                    )
                if fl is not None:
                    ok, found = await is_train_watering_form(fl)
                    if ok:
                        log_automation_event(
                            logger,
                            "report14_form_frame_resolved",
                            found=found[:12],
                            frame_url=frame.url,
                        )
                        return fl
            except Exception:
                continue
    except Exception:
        pass

    from app.automation.selectors import selectors

    for frame_selector in (selectors.report1_frame or "").split(","):
        frame_selector = frame_selector.strip()
        if not frame_selector:
            continue
        try:
            fl = page.frame_locator(frame_selector).first
            ok, found = await is_train_watering_form(fl)
            if ok:
                log_automation_event(
                    logger,
                    "report14_form_frame_resolved",
                    found=found[:12],
                    frame_selector=frame_selector,
                )
                return fl
        except Exception:
            continue

    ok, found = await is_train_watering_form(page)
    if ok:
        log_automation_event(
            logger,
            "report14_form_main_page_resolved",
            found=found[:12],
        )
        return page
    return None


async def wait_for_report14_form(page: Page, *, timeout_ms: int = 25_000) -> Page | FrameLocator:
    """Poll until Train Watering (tab 11) form is visible in page or iframe."""
    deadline_slices = max(timeout_ms // 500, 10)
    last_score = 0
    last_found: list[str] = []
    for _ in range(deadline_slices):
        ctx = await resolve_report14_form_context(page)
        if ctx is not None:
            return ctx
        score, found = await _count_form_signals(page)
        last_score, last_found = score, found
        try:
            await page.wait_for_timeout(500)
        except Exception:
            pass
    log_automation_event(
        logger,
        "report14_form_wait_timeout",
        last_score=last_score,
        last_found=last_found,
        url=page.url,
    )
    raise Report14NavigationError(NAV_ERROR_MESSAGE)


async def navigate_report14_via_menu(
    page: Page,
    *,
    run_id: str = "",
) -> Page | FrameLocator:
    """Always open tab 11) Train Watering Complaint only — never Inquiry Wise / other tabs.

    Menu path only (no URL-only success). Returns page/frame with the watering form.
    """
    log_automation_event(
        logger,
        "report14_menu_navigation_started",
        url=page.url,
        run_id=run_id,
        target_tab=TAB11_MENU_LABEL,
    )

    # Skip menu only when Train Watering form is already confirmed (re-extract).
    try:
        existing = await resolve_report14_form_context(page)
        if existing is not None:
            log_automation_event(
                logger,
                "report14_form_already_loaded",
                url=page.url,
                run_id=run_id,
                target_tab=TAB11_MENU_LABEL,
            )
            return existing
    except Exception:
        pass

    # 1) Admin shell ready
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=15_000)
    except PlaywrightTimeoutError:
        pass
    try:
        await page.get_by_text("MIS Reports", exact=True).first.wait_for(
            state="visible", timeout=20_000
        )
    except Exception as exc:
        await _save_nav_diagnostics(page, run_id=run_id or "na", reason="no_mis_shell")
        raise Report14NavigationError(
            f"{NAV_ERROR_MESSAGE} (admin shell / MIS Reports not ready: {exc})"
        ) from exc

    # 2) Expand MIS Reports if needed
    expanded = await ensure_mis_reports_expanded(page)
    if not expanded:
        await _save_nav_diagnostics(
            page, run_id=run_id or "na", reason="submenu_not_expanded", mis_expanded=False
        )
        raise Report14NavigationError(
            f"{NAV_ERROR_MESSAGE} (MIS Reports submenu did not expand)."
        )

    # 3) Click tab 11 only (with one expand+retry cycle)
    clicked = await click_tab11_train_watering(page)
    if not clicked:
        await ensure_mis_reports_expanded(page)
        clicked = await click_tab11_train_watering(page)
    if not clicked:
        await _save_nav_diagnostics(
            page,
            run_id=run_id or "na",
            reason="tab11_not_found",
            mis_expanded=True,
            tab11_clicked=False,
        )
        raise Report14NavigationError(
            f"{NAV_ERROR_MESSAGE} (menu item '{TAB11_MENU_LABEL}' not found)."
        )

    # 4) Wait for Train Watering form only (never accept a different report form)
    try:
        form_ctx = await wait_for_report14_form(page)
    except Report14NavigationError:
        await _save_nav_diagnostics(
            page,
            run_id=run_id or "na",
            reason="form_blank_after_tab11",
            mis_expanded=True,
            tab11_clicked=True,
        )
        raise

    log_automation_event(
        logger,
        "report14_menu_navigation_succeeded",
        url=page.url,
        run_id=run_id,
        target_tab=TAB11_MENU_LABEL,
    )
    return form_ctx
