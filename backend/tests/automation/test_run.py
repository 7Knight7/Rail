"""Unit tests for automation run entrypoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.automation.browser import BrowserConnectionError
from app.automation.run import run


@pytest.mark.asyncio
async def test_run_returns_true_on_success(caplog: pytest.LogCaptureFixture):
    mock_manager = MagicMock()
    mock_manager.connect = AsyncMock()
    mock_manager.close = AsyncMock()

    with (
        patch("app.automation.run.BrowserManager", return_value=mock_manager),
        caplog.at_level("INFO"),
    ):
        result = await run()

    assert result is True
    mock_manager.connect.assert_awaited_once()
    mock_manager.close.assert_awaited_once()
    assert "Connected successfully" in caplog.text


@pytest.mark.asyncio
async def test_run_closes_on_connect_failure():
    mock_manager = MagicMock()
    mock_manager.connect = AsyncMock(side_effect=BrowserConnectionError("Connection refused"))
    mock_manager.close = AsyncMock()

    with patch("app.automation.run.BrowserManager", return_value=mock_manager):
        with pytest.raises(BrowserConnectionError, match="Connection refused"):
            await run()

    mock_manager.close.assert_awaited_once()
