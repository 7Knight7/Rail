"""CDP attach entrypoint: connect, discover tabs, activate RailMadad tab."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from app.automation.browser import BrowserConnectionError, BrowserManager
from app.automation.config import config
from app.automation.filters import FilterDiscoveryService, FilterError, FilterService
from app.automation.generator import ReportGenerationError, ReportGeneratorService
from app.automation.navigation import NavigationError, NavigationService
from app.automation.report1_filters import (
    applied_filter_records,
    build_filters_from_discovery,
)
from app.automation.reports import catalog
from app.automation.schemas import AutomationStartResult
from app.automation.session import RailMadadTabNotFoundError, SessionManager, TabInfo
from app.automation.utils import log_automation_event

logger = logging.getLogger(__name__)


def _log_tab(tab: TabInfo) -> None:
    log_automation_event(
        logger,
        "tab_discovered",
        context_index=tab.context_index,
        tab_index=tab.tab_index,
        url=tab.url,
        title=tab.title,
        is_railmadad=tab.is_railmadad,
    )
    logger.info("%s", tab.format_line())


async def _capture_failure_screenshot(
    session: SessionManager,
    tabs: list[TabInfo],
) -> str | None:
    page = session.first_available_page(tabs)
    if page is None:
        return None
    try:
        return await session.capture_screenshot(page, Path(config.screenshots_dir))
    except Exception as exc:
        logger.warning("Could not capture failure screenshot: %s", exc)
        return None


async def attach_to_railmadad() -> AutomationStartResult:
    """Connect to Chrome over CDP, list tabs, and bring RailMadad tab to front."""
    manager = BrowserManager(cdp_url=config.chrome_debug_url)
    session = SessionManager(railmadad_url=config.railmadad_url)
    tabs: list[TabInfo] = []
    connected = False

    try:
        log_automation_event(
            logger,
            "cdp_connect_attempt",
            cdp_url=config.chrome_debug_url,
        )
        browser = await manager.connect()
        connected = True
        log_automation_event(
            logger,
            "cdp_connected",
            cdp_url=config.chrome_debug_url,
            context_count=len(browser.contexts),
        )

        tabs = await session.discover_tabs(browser)
        for tab in tabs:
            _log_tab(tab)

        railmadad_tab = session.find_railmadad_tab(
            tabs,
            prefer_url_fragment=catalog.first_report().url_fragment,
        )
        if railmadad_tab is None:
            screenshot_path = await _capture_failure_screenshot(session, tabs)
            error = "RailMadad tab not found among open tabs"
            log_automation_event(
                logger,
                "railmadad_tab_not_found",
                tab_count=len(tabs),
                screenshot_path=screenshot_path,
                error=error,
            )
            return AutomationStartResult(
                success=False,
                connected=True,
                tab_found=False,
                error=error,
            )

        await session.activate_tab(railmadad_tab.page)
        log_automation_event(
            logger,
            "railmadad_tab_activated",
            context_index=railmadad_tab.context_index,
            tab_index=railmadad_tab.tab_index,
            url=railmadad_tab.url,
            title=railmadad_tab.title,
        )
        logger.info("RailMadad tab activated: %s", railmadad_tab.format_line())

        page = railmadad_tab.page
        report = catalog.first_report()
        navigation = NavigationService()

        await navigation.navigate_to_report(page, report)

        screenshot_path = await navigation.capture_debug_screenshot(
            page,
            config.debug_screenshots_dir,
            report.screenshot_filename,
        )

        filter_service = FilterService()
        discovery = FilterDiscoveryService()
        generator = ReportGeneratorService()

        report_root = await filter_service.get_report_root(page)
        discovered_fields = await discovery.discover_fields(page)
        report_filters = build_filters_from_discovery(discovered_fields, report.slug)
        applied_values = await filter_service.apply_filters(
            report_root,
            report_filters,
            page=page,
        )
        await filter_service.validate_mandatory(report_root, report_filters, applied_values)

        screenshot_before = await generator.capture_before_generate(page)
        await generator.generate_report(report_root, page)
        row_count = await generator.count_rows(report_root)
        if not await generator.verify_report_displayed(report_root):
            raise ReportGenerationError("Report did not display after generate")
        await generator.log_report_metadata(page, row_count)
        screenshot_after = await generator.capture_report_loaded(page)

        try:
            final_title = await page.title()
        except Exception:
            final_title = railmadad_tab.title

        return AutomationStartResult(
            success=True,
            connected=True,
            tab_found=True,
            url=page.url,
            title=final_title,
            report_reached=True,
            report_name=report.name,
            screenshot_path=screenshot_path,
            report_generated=True,
            filters_applied=applied_filter_records(report_filters, applied_values),
            row_count=row_count,
            screenshot_before_path=screenshot_before,
            screenshot_after_path=screenshot_after,
        )

    except (FilterError, ReportGenerationError) as exc:
        logger.error("Report filter/generation failed", exc_info=True)
        screenshot_path = await _capture_failure_screenshot(session, tabs)
        return AutomationStartResult(
            success=False,
            connected=connected,
            tab_found=True,
            error=exc.message,
            report_reached=True,
            screenshot_path=screenshot_path,
        )

    except NavigationError as exc:
        logger.error("Report navigation failed", exc_info=True)
        screenshot_path = await _capture_failure_screenshot(session, tabs)
        return AutomationStartResult(
            success=False,
            connected=connected,
            tab_found=True,
            error=exc.message,
            screenshot_path=screenshot_path,
        )

    except BrowserConnectionError as exc:
        logger.error(
            "CDP connection failed at %s",
            config.chrome_debug_url,
            exc_info=True,
        )
        return AutomationStartResult(
            success=False,
            connected=False,
            tab_found=False,
            error=exc.message,
        )
    except RailMadadTabNotFoundError as exc:
        screenshot_path = await _capture_failure_screenshot(session, tabs)
        log_automation_event(
            logger,
            "attach_failed",
            error=str(exc),
            screenshot_path=screenshot_path,
        )
        return AutomationStartResult(
            success=False,
            connected=connected,
            tab_found=False,
            error=str(exc),
        )
    except Exception as exc:
        logger.exception("Automation attach run failed")
        screenshot_path = await _capture_failure_screenshot(session, tabs)
        log_automation_event(
            logger,
            "attach_failed",
            error=str(exc),
            screenshot_path=screenshot_path,
        )
        tab_found = connected and any(tab.is_railmadad for tab in tabs)
        return AutomationStartResult(
            success=False,
            connected=connected,
            tab_found=tab_found,
            error=str(exc),
            report_reached=tab_found,
            screenshot_path=screenshot_path,
        )
    finally:
        log_automation_event(
            logger,
            "cdp_disconnect_start",
            browser_connected=manager.browser is not None,
            cdp_url=config.chrome_debug_url,
        )
        await manager.close()
        log_automation_event(logger, "cdp_disconnected")


async def run() -> bool:
    """CLI/debug entrypoint — returns True when attach succeeded."""
    result = await attach_to_railmadad()
    return result.success


async def main() -> None:
    success = await run()
    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
