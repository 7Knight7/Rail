"""Unit tests for in-process automation API."""

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.automation.dependencies import get_automation_service
from app.main import app


@pytest.fixture
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_start_automation_success(api_client: AsyncClient):
    mock_service = AsyncMock()
    app.dependency_overrides[get_automation_service] = lambda: mock_service

    response = await api_client.post("/api/v1/automation/start")

    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Automation started"}
    mock_service.start.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_automation_returns_500_on_failure(api_client: AsyncClient):
    mock_service = AsyncMock()
    mock_service.start.side_effect = RuntimeError("boom")
    app.dependency_overrides[get_automation_service] = lambda: mock_service

    response = await api_client.post("/api/v1/automation/start")

    assert response.status_code == 500
