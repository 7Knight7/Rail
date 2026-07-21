"""Unit tests for BrowserManager CDP connection."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.automation.browser import (
    DEFAULT_CDP_URL,
    BrowserConnectionError,
    BrowserManager,
    _log_browser_state,
    ensure_edge_cdp_ready,
)


def _mock_playwright_stack(*, connect_side_effect=None):
    """Build mocked async_playwright().start() returning playwright with chromium."""
    mock_page = MagicMock()
    mock_page.url = "https://example.com"

    mock_context = MagicMock()
    mock_context.pages = [mock_page]

    mock_browser = MagicMock()
    mock_browser.contexts = [mock_context]
    mock_browser.close = AsyncMock()

    mock_chromium = MagicMock()
    if connect_side_effect is not None:
        mock_chromium.connect_over_cdp = AsyncMock(side_effect=connect_side_effect)
    else:
        mock_chromium.connect_over_cdp = AsyncMock(return_value=mock_browser)

    mock_playwright = MagicMock()
    mock_playwright.chromium = mock_chromium
    mock_playwright.stop = AsyncMock()

    mock_starter = MagicMock()
    mock_starter.start = AsyncMock(return_value=mock_playwright)

    return mock_starter, mock_playwright, mock_chromium, mock_browser


def test_log_browser_state_logs_contexts_and_urls(caplog: pytest.LogCaptureFixture):
    mock_page = MagicMock()
    mock_page.url = "https://railmadad.indianrail.gov.in/"

    mock_context = MagicMock()
    mock_context.pages = [mock_page]

    mock_browser = MagicMock()
    mock_browser.contexts = [mock_context]

    with caplog.at_level("INFO"):
        _log_browser_state(mock_browser, "test_stage")

    assert "CDP browser state [test_stage]: 1 context(s), 1 page(s)" in caplog.text
    assert "url=https://railmadad.indianrail.gov.in/" in caplog.text


@pytest.mark.asyncio
async def test_connect_returns_browser():
    mock_starter, _mock_pw, mock_chromium, mock_browser = _mock_playwright_stack()

    with patch("app.automation.browser.async_playwright", return_value=mock_starter), patch(
        "app.automation.browser.ensure_edge_cdp_ready", new_callable=AsyncMock
    ):
        manager = BrowserManager()
        browser = await manager.connect()

    assert browser is mock_browser
    mock_chromium.connect_over_cdp.assert_awaited_once_with(DEFAULT_CDP_URL)
    assert manager.browser is mock_browser


@pytest.mark.asyncio
async def test_connect_raises_when_already_connected():
    mock_starter, _mock_pw, _mock_chromium, mock_browser = _mock_playwright_stack()

    with patch("app.automation.browser.async_playwright", return_value=mock_starter), patch(
        "app.automation.browser.ensure_edge_cdp_ready", new_callable=AsyncMock
    ):
        manager = BrowserManager()
        await manager.connect()

        with pytest.raises(BrowserConnectionError, match="already connected"):
            await manager.connect()

    await manager.close()


@pytest.mark.asyncio
async def test_connect_raises_on_cdp_failure():
    mock_starter, mock_playwright, _mock_chromium, _mock_browser = _mock_playwright_stack(
        connect_side_effect=Exception("Connection refused"),
    )

    with patch("app.automation.browser.async_playwright", return_value=mock_starter), patch(
        "app.automation.browser.ensure_edge_cdp_ready", new_callable=AsyncMock
    ):
        manager = BrowserManager()
        with pytest.raises(BrowserConnectionError, match="Cannot connect to browser CDP"):
            await manager.connect()

    mock_playwright.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_is_idempotent():
    mock_starter, _mock_pw, _mock_chromium, _mock_browser = _mock_playwright_stack()

    with patch("app.automation.browser.async_playwright", return_value=mock_starter):
        manager = BrowserManager()
        await manager.close()
        await manager.close()

    _mock_browser.close.assert_not_awaited()


@pytest.mark.asyncio
async def test_close_cleans_up():
    mock_starter, mock_playwright, _mock_chromium, mock_browser = _mock_playwright_stack()

    with patch("app.automation.browser.async_playwright", return_value=mock_starter), patch(
        "app.automation.browser.ensure_edge_cdp_ready", new_callable=AsyncMock
    ):
        manager = BrowserManager()
        await manager.connect()
        await manager.close()

    mock_browser.close.assert_not_awaited()
    mock_playwright.stop.assert_awaited_once()
    assert manager.browser is None


@pytest.mark.asyncio
async def test_ensure_edge_cdp_ready_launches_edge_when_probe_fails(monkeypatch: pytest.MonkeyPatch):
    probe_calls = {"count": 0}

    async def fake_probe(_cdp_url: str, *, timeout: float = 2.0) -> None:
        probe_calls["count"] += 1
        if probe_calls["count"] == 1:
            raise BrowserConnectionError("down")

    launched: list[list[str]] = []

    def fake_popen(args, **_kwargs):
        launched.append(list(args))
        return MagicMock()

    monkeypatch.setattr("app.automation.browser.probe_cdp_reachable", fake_probe)
    monkeypatch.setattr("app.automation.browser._close_stale_edge_debug_processes", lambda _profile: None)
    monkeypatch.setattr("app.automation.browser.subprocess.Popen", fake_popen)
    monkeypatch.setattr("app.automation.browser.asyncio.sleep", AsyncMock())

    await ensure_edge_cdp_ready(DEFAULT_CDP_URL, auto_launch=True)

    assert probe_calls["count"] >= 2
    assert launched
    assert any(str(arg[0]).endswith("msedge.exe") for arg in launched)
    edge_args = next(arg for arg in launched if str(arg[0]).endswith("msedge.exe"))
    assert "--remote-debugging-port=9222" in edge_args
    assert "--user-data-dir=C:\\EdgeDebug" in edge_args
