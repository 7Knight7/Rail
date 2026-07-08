"""Unit tests for report generation service."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.automation.generator import ReportGenerationError, ReportGeneratorService


@pytest.mark.asyncio
async def test_generate_report_clicks_visible_button():
    service = ReportGeneratorService()
    frame = MagicMock()
    page = MagicMock()
    page.wait_for_load_state = AsyncMock()

    button = MagicMock()
    button.is_visible = AsyncMock(return_value=True)
    button.click = AsyncMock()

    submit_locator = MagicMock()
    submit_locator.count = AsyncMock(return_value=1)
    submit_locator.nth.return_value = button

    table = MagicMock()
    table.count = AsyncMock(return_value=1)
    table.wait_for = AsyncMock()
    table.first = table

    def locator_side_effect(selector):
        if any(token in selector for token in ("loading", "loader", "spinner", "Loader")):
            empty = MagicMock()
            empty.count = AsyncMock(return_value=0)
            return empty
        if "table" in selector or "grid" in selector:
            return table
        return submit_locator

    frame.locator.side_effect = locator_side_effect

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(service, "_is_export_button", AsyncMock(return_value=False))
        await service.generate_report(frame, page)

    button.click.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_report_raises_when_no_button():
    service = ReportGeneratorService()
    frame = MagicMock()
    page = MagicMock()

    empty = MagicMock()
    empty.count = AsyncMock(return_value=0)
    empty.nth.return_value = empty
    frame.locator.return_value = empty

    with pytest.raises(ReportGenerationError, match="button not found"):
        await service.generate_report(frame, page)


@pytest.mark.asyncio
async def test_count_rows():
    service = ReportGeneratorService()
    root = MagicMock()

    table = MagicMock()
    table.count = AsyncMock(return_value=1)

    rows = MagicMock()
    rows.count = AsyncMock(return_value=5)

    table_wrapper = MagicMock()
    table_wrapper.first = table

    def locator_side_effect(selector):
        if selector.endswith("tbody tr"):
            return rows
        return table_wrapper

    root.locator.side_effect = locator_side_effect

    assert await service.count_rows(root) == 5
