"""CDP attach entrypoint: connect, discover tabs, run multi-report automation."""

from __future__ import annotations

import asyncio
import logging

from app.automation.browser import BrowserConnectionError, BrowserManager
from app.automation.config import config
from app.automation.handlers import get_handler
from app.automation.report_keys import canonicalize_report_key
from app.automation.reports import catalog
from app.automation.schemas import MultiReportResult, ReportResult
from app.automation.session import (
    MisSessionError,
    RailMadadTabNotFoundError,
    SessionManager,
    TabInfo,
)
from app.automation.utils import log_automation_event
from app.automation.workflow import (
    FEEDBACK_DATASET_ID,
    FEEDBACK_ZONE_FILENAME,
    attempt_feedback_extract,
    extract_feedback_zone_csv,
    extract_with_retry,
    ingest_downloaded_file,
    regenerate_comprehensive_for_pdf,
    save_failure_artifacts,
    verify_mis_session_or_raise,
)

logger = logging.getLogger(__name__)

# Backward-compatible aliases for tests importing from run.py
_ingest_downloaded_file = ingest_downloaded_file
_verify_mis_session_or_raise = verify_mis_session_or_raise
_extract_with_retry = extract_with_retry
_attempt_feedback_extract = attempt_feedback_extract
_extract_feedback_zone_csv = extract_feedback_zone_csv
_regenerate_comprehensive_for_pdf = regenerate_comprehensive_for_pdf
_save_failure_artifacts = save_failure_artifacts


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
        from pathlib import Path

        return await session.capture_screenshot(page, Path(config.screenshots_dir))
    except Exception as exc:
        logger.warning("Could not capture failure screenshot: %s", exc)
        return None


async def attach_to_railmadad() -> MultiReportResult:
    """Connect to Chrome over CDP and execute all catalog reports sequentially."""
    manager = BrowserManager(cdp_url=config.chrome_debug_url)
    session = SessionManager(railmadad_url=config.railmadad_url)
    tabs: list[TabInfo] = []
    connected = False
    report_results: list[ReportResult] = []

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

        page = await session.ensure_authenticated_mis_page(
            browser,
            prefer_url_fragment=catalog.first_report().url_fragment,
        )
        log_automation_event(
            logger,
            "railmadad_tab_activated",
            url=page.url,
        )
        logger.info("RailMadad MIS tab activated: %s", page.url)

        if await session.is_login_page(page):
            return MultiReportResult(
                success=False,
                connected=True,
                tab_found=True,
                error="Please log in to RailMadad before generating reports.",
                error_code="RAILMADAD_NOT_LOGGED_IN",
            )

        log_automation_event(logger, "phase9_validation_started")

        for report in catalog.reports:
            slug = canonicalize_report_key(report.slug)
            log_automation_event(logger, "report_started", slug=slug)

            try:
                page = await session.ensure_authenticated_mis_page(browser, page)
                handler = get_handler(slug)
                handler.bind_browser(browser)
                result = await handler.execute(page, session, report)
                report_results.append(result)

                # Keep page reference fresh after each report
                page = await session.ensure_authenticated_mis_page(browser, page)

                if result.status == "success":
                    log_automation_event(
                        logger,
                        "report_completed",
                        slug=slug,
                        status=result.status,
                        pdf_download_url=result.pdf_download_url,
                    )
                else:
                    log_automation_event(
                        logger,
                        "report_failed",
                        slug=slug,
                        status=result.status,
                        error=result.error,
                    )

            except MisSessionError as exc:
                failed_result = ReportResult(
                    slug=slug,
                    dataset_key=slug,
                    status="failed",
                    error=exc.status.error,
                )
                report_results.append(failed_result)
                log_automation_event(
                    logger,
                    "report_failed",
                    slug=slug,
                    error="auth_lost",
                    error_code=exc.status.error_code,
                )
                return MultiReportResult(
                    success=False,
                    connected=True,
                    tab_found=True,
                    reports=report_results,
                    stopped_early=True,
                    stop_reason=exc.status.error_code or "MIS_SESSION_LOST",
                    error=exc.status.error,
                    error_code=exc.status.error_code,
                    session_valid=False,
                )

            except Exception as exc:
                logger.exception("Report %s failed", slug)
                report_results.append(
                    ReportResult(
                        slug=slug,
                        dataset_key=slug,
                        status="failed",
                        error=str(exc),
                    )
                )
                log_automation_event(
                    logger,
                    "report_failed",
                    slug=slug,
                    error=str(exc),
                )
                # Non-auth failure: try to reacquire MIS and continue
                try:
                    page = await session.ensure_authenticated_mis_page(browser, page)
                except MisSessionError as auth_exc:
                    return MultiReportResult(
                        success=False,
                        connected=True,
                        tab_found=True,
                        reports=report_results,
                        stopped_early=True,
                        stop_reason=auth_exc.status.error_code or "MIS_SESSION_LOST",
                        error=auth_exc.status.error,
                        error_code=auth_exc.status.error_code,
                        session_valid=False,
                    )

        overall_success = all(r.status == "success" for r in report_results)
        log_automation_event(
            logger,
            "multi_report_run_complete",
            success=overall_success,
            report_count=len(report_results),
        )

        return MultiReportResult(
            success=overall_success,
            connected=True,
            tab_found=True,
            reports=report_results,
            session_valid=True,
        )

    except MisSessionError as exc:
        logger.error("MIS session lost or invalid", exc_info=True)
        await _capture_failure_screenshot(session, tabs)
        return MultiReportResult(
            success=False,
            connected=connected,
            tab_found=True,
            reports=report_results,
            error=exc.status.error,
            error_code=exc.status.error_code,
            session_valid=False,
            stopped_early=True,
            stop_reason=exc.status.error_code or "MIS_SESSION_LOST",
        )

    except BrowserConnectionError as exc:
        logger.error(
            "CDP connection failed at %s",
            config.chrome_debug_url,
            exc_info=True,
        )
        return MultiReportResult(
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
        return MultiReportResult(
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
        return MultiReportResult(
            success=False,
            connected=connected,
            tab_found=tab_found,
            reports=report_results,
            error=str(exc),
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
