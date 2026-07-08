"""Unit tests for automation run entrypoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.automation.browser import BrowserConnectionError
from app.automation.run import attach_to_railmadad, run
from app.automation.schemas import AutomationStartResult
from app.automation.session import TabInfo


def _railmadad_tab() -> TabInfo:
    page = MagicMock()
    page.bring_to_front = AsyncMock()
    page.url = (
        "https://railmadad.indianrailways.gov.in/rmmis/admin/home.jsp"
        "?page=/mis_reports/report1&archiveFlag=N"
    )
    page.title = AsyncMock(return_value="RailMadad")
    return TabInfo(
        context_index=0,
        tab_index=0,
        url=page.url,
        title="RailMadad",
        is_railmadad=True,
        page=page,
    )


def _google_tab() -> TabInfo:
    page = MagicMock()
    page.screenshot = AsyncMock()
    return TabInfo(
        context_index=0,
        tab_index=1,
        url="https://google.com",
        title="Google",
        is_railmadad=False,
        page=page,
    )


def _phase5_mocks():
    mock_frame = MagicMock()
    mock_filter_service = MagicMock()
    mock_filter_service.get_report_root = AsyncMock(return_value=mock_frame)
    mock_filter_service.apply_filters = AsyncMock(
        return_value={"dateRange": "Current Day"},
    )
    mock_filter_service.validate_mandatory = AsyncMock()

    mock_discovery = MagicMock()
    mock_discovery.discover_fields = AsyncMock(
        return_value=[
            {
                "tag": "select",
                "field_id": "dateRange",
                "field_name": "dateRange",
                "field_type": "select-one",
                "field_label": "Date Range",
                "selector": "#dateRange",
                "current_value": "Previous Day",
                "required": False,
                "options": [],
            }
        ],
    )

    mock_generator = MagicMock()
    mock_generator.capture_before_generate = AsyncMock(
        return_value="storage/debug/phase5_before_generate.png",
    )
    mock_generator.generate_report = AsyncMock()
    mock_generator.count_rows = AsyncMock(return_value=3)
    mock_generator.verify_report_displayed = AsyncMock(return_value=True)
    mock_generator.log_report_metadata = AsyncMock()
    mock_generator.capture_report_loaded = AsyncMock(
        return_value="storage/debug/phase5_report_loaded.png",
    )

    return mock_filter_service, mock_discovery, mock_generator


@pytest.mark.asyncio
async def test_attach_returns_success_when_railmadad_tab_found():
    mock_manager = MagicMock()
    mock_manager.connect = AsyncMock(return_value=MagicMock(contexts=[MagicMock()]))
    mock_manager.close = AsyncMock()
    mock_manager.browser = MagicMock()

    mock_session = MagicMock()
    railmadad = _railmadad_tab()
    mock_session.discover_tabs = AsyncMock(return_value=[railmadad])
    mock_session.find_railmadad_tab = MagicMock(return_value=railmadad)
    mock_session.activate_tab = AsyncMock()

    mock_navigation = MagicMock()
    mock_navigation.navigate_to_report = AsyncMock()
    mock_navigation.capture_debug_screenshot = AsyncMock(return_value="storage/debug/report1.png")

    mock_filter_service, mock_discovery, mock_generator = _phase5_mocks()

    with (
        patch("app.automation.run.BrowserManager", return_value=mock_manager),
        patch("app.automation.run.SessionManager", return_value=mock_session),
        patch("app.automation.run.NavigationService", return_value=mock_navigation),
        patch("app.automation.run.FilterService", return_value=mock_filter_service),
        patch("app.automation.run.FilterDiscoveryService", return_value=mock_discovery),
        patch("app.automation.run.ReportGeneratorService", return_value=mock_generator),
    ):
        result = await attach_to_railmadad()

    assert result == AutomationStartResult(
        success=True,
        connected=True,
        tab_found=True,
        url=railmadad.page.url,
        title="RailMadad",
        report_reached=True,
        report_name="MIS Report 1",
        screenshot_path="storage/debug/report1.png",
        report_generated=True,
        filters_applied=[
            {"name": "dateRange", "value": "Current Day", "label": "Date Range"},
        ],
        row_count=3,
        screenshot_before_path="storage/debug/phase5_before_generate.png",
        screenshot_after_path="storage/debug/phase5_report_loaded.png",
    )
    mock_manager.connect.assert_awaited_once()
    mock_session.activate_tab.assert_awaited_once_with(railmadad.page)
    mock_navigation.navigate_to_report.assert_awaited_once()
    mock_navigation.capture_debug_screenshot.assert_awaited_once()
    mock_discovery.discover_fields.assert_awaited_once()
    mock_filter_service.apply_filters.assert_awaited_once()
    mock_generator.generate_report.assert_awaited_once()
    mock_manager.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_attach_returns_failure_when_filter_fails():
    mock_manager = MagicMock()
    mock_manager.connect = AsyncMock(return_value=MagicMock(contexts=[MagicMock()]))
    mock_manager.close = AsyncMock()
    mock_manager.browser = MagicMock()

    mock_session = MagicMock()
    railmadad = _railmadad_tab()
    mock_session.discover_tabs = AsyncMock(return_value=[railmadad])
    mock_session.find_railmadad_tab = MagicMock(return_value=railmadad)
    mock_session.activate_tab = AsyncMock()
    mock_session.first_available_page = MagicMock(return_value=railmadad.page)
    mock_session.capture_screenshot = AsyncMock(return_value="/tmp/failure.png")

    mock_navigation = MagicMock()
    mock_navigation.navigate_to_report = AsyncMock()
    mock_navigation.capture_debug_screenshot = AsyncMock(return_value="storage/debug/report1.png")

    mock_filter_service, mock_discovery, mock_generator = _phase5_mocks()
    from app.automation.filters import FilterError

    mock_filter_service.apply_filters = AsyncMock(
        side_effect=FilterError("Mandatory filters missing or empty: fromDate"),
    )

    with (
        patch("app.automation.run.BrowserManager", return_value=mock_manager),
        patch("app.automation.run.SessionManager", return_value=mock_session),
        patch("app.automation.run.NavigationService", return_value=mock_navigation),
        patch("app.automation.run.FilterService", return_value=mock_filter_service),
        patch("app.automation.run.FilterDiscoveryService", return_value=mock_discovery),
        patch("app.automation.run.ReportGeneratorService", return_value=mock_generator),
    ):
        result = await attach_to_railmadad()

    assert result.success is False
    assert result.report_reached is True
    assert "Mandatory filters missing" in (result.error or "")
    mock_generator.generate_report.assert_not_called()
    mock_manager.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_attach_returns_failure_when_navigation_fails():
    mock_manager = MagicMock()
    mock_manager.connect = AsyncMock(return_value=MagicMock(contexts=[MagicMock()]))
    mock_manager.close = AsyncMock()
    mock_manager.browser = MagicMock()

    mock_session = MagicMock()
    railmadad = _railmadad_tab()
    mock_session.discover_tabs = AsyncMock(return_value=[railmadad])
    mock_session.find_railmadad_tab = MagicMock(return_value=railmadad)
    mock_session.activate_tab = AsyncMock()
    mock_session.first_available_page = MagicMock(return_value=railmadad.page)
    mock_session.capture_screenshot = AsyncMock(return_value="/tmp/failure.png")

    mock_navigation = MagicMock()
    from app.automation.navigation import NavigationError

    mock_navigation.navigate_to_report = AsyncMock(
        side_effect=NavigationError("Report page verification failed"),
    )

    with (
        patch("app.automation.run.BrowserManager", return_value=mock_manager),
        patch("app.automation.run.SessionManager", return_value=mock_session),
        patch("app.automation.run.NavigationService", return_value=mock_navigation),
    ):
        result = await attach_to_railmadad()

    assert result.success is False
    assert result.connected is True
    assert result.tab_found is True
    assert result.error == "Report page verification failed"
    assert result.screenshot_path == "/tmp/failure.png"
    mock_manager.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_attach_returns_failure_when_railmadad_tab_missing():
    mock_manager = MagicMock()
    mock_manager.connect = AsyncMock(return_value=MagicMock(contexts=[MagicMock()]))
    mock_manager.close = AsyncMock()
    mock_manager.browser = MagicMock()

    mock_session = MagicMock()
    google = _google_tab()
    mock_session.discover_tabs = AsyncMock(return_value=[google])
    mock_session.find_railmadad_tab = MagicMock(return_value=None)
    mock_session.first_available_page = MagicMock(return_value=google.page)
    mock_session.capture_screenshot = AsyncMock(return_value="/tmp/failure.png")

    with (
        patch("app.automation.run.BrowserManager", return_value=mock_manager),
        patch("app.automation.run.SessionManager", return_value=mock_session),
    ):
        result = await attach_to_railmadad()

    assert result.success is False
    assert result.connected is True
    assert result.tab_found is False
    mock_session.activate_tab.assert_not_called()
    mock_manager.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_attach_returns_failure_on_connect_error():
    mock_manager = MagicMock()
    mock_manager.connect = AsyncMock(
        side_effect=BrowserConnectionError("Connection refused"),
    )
    mock_manager.close = AsyncMock()
    mock_manager.browser = None

    with patch("app.automation.run.BrowserManager", return_value=mock_manager):
        result = await attach_to_railmadad()

    assert result == AutomationStartResult(
        success=False,
        connected=False,
        tab_found=False,
        error="Connection refused",
    )
    mock_manager.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_returns_true_when_attach_succeeds():
    with patch(
        "app.automation.run.attach_to_railmadad",
        AsyncMock(
            return_value=AutomationStartResult(
                success=True,
                connected=True,
                tab_found=True,
                url="https://railmadad.indianrail.gov.in/",
                title="RailMadad",
            )
        ),
    ):
        assert await run() is True


@pytest.mark.asyncio
async def test_run_returns_false_when_attach_fails():
    with patch(
        "app.automation.run.attach_to_railmadad",
        AsyncMock(
            return_value=AutomationStartResult(
                success=False,
                connected=False,
                tab_found=False,
                error="Connection refused",
            )
        ),
    ):
        assert await run() is False
