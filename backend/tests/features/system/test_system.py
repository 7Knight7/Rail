"""Integration tests for the system info/maintenance API."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

import app.features.system.service as system_service
from app.core.security.password import password_hasher
from app.infrastructure.database.models import UserModel


@pytest.fixture(autouse=True)
def cdp_down(monkeypatch):
    """Make the CDP probe fail fast and deterministically."""

    class _FailingClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url):
            raise ConnectionError("CDP not running")

    monkeypatch.setattr(system_service.httpx, "AsyncClient", _FailingClient)


@pytest.fixture
async def admin_user(test_session: AsyncSession) -> UserModel:
    user = UserModel(
        id="admin-system-id",
        username="systemadmin",
        email="systemadmin@example.com",
        password_hash=password_hasher.hash("TestPass123"),
        role="admin",
        is_active=True,
    )
    test_session.add(user)
    await test_session.commit()
    return user


@pytest.fixture
async def admin_client(client: AsyncClient, admin_user: UserModel) -> tuple[AsyncClient, dict]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "systemadmin", "password": "TestPass123"},
    )
    assert response.status_code == 200
    csrf = response.json().get("csrf_token")
    headers = {"X-CSRF-Token": csrf} if csrf else {}
    return client, headers


@pytest.mark.asyncio
async def test_system_info_requires_auth(client):
    response = await client.get("/api/v1/system/info")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_system_info_forbidden_for_viewer(authenticated_client):
    response = await authenticated_client.get("/api/v1/system/info")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_system_info_shape(admin_client):
    client, _ = admin_client
    response = await client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()

    assert data["backend"]["ok"] is True
    assert data["database"]["ok"] is True
    assert data["cdp"]["ok"] is False
    assert data["automation_status"] == "idle"
    assert data["app_version"]
    assert data["environment"]
    assert isinstance(data["storage_usage_bytes"], int)
    assert data["last_successful_run_at"] is None
    assert data["last_failed_run_at"] is None


@pytest.mark.asyncio
async def test_clear_cache(admin_client):
    client, headers = admin_client
    response = await client.post("/api/v1/system/clear-cache", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert set(data["cleared"]) == {"settings", "dashboard_analytics"}


@pytest.mark.asyncio
async def test_clear_cache_forbidden_for_viewer(authenticated_client):
    response = await authenticated_client.post("/api/v1/system/clear-cache")
    assert response.status_code in (400, 403)
