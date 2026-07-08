"""Unit tests for in-process AutomationService."""

from unittest.mock import patch

import pytest

from app.automation.schemas import AutomationStartResult
from app.automation.service import AutomationService


@pytest.mark.asyncio
async def test_start_delegates_to_attach_runner():
    expected = AutomationStartResult(
        success=True,
        connected=True,
        tab_found=True,
        url="https://railmadad.indianrail.gov.in/",
        title="RailMadad",
    )
    with patch(
        "app.automation.service._run_attach_in_thread",
        return_value=expected,
    ) as mock_runner:
        result = await AutomationService().start()

    assert result == expected
    mock_runner.assert_called_once()
