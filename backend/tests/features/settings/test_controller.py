"""Integration tests for settings API."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.password import password_hasher
from app.features.settings.seeds.default_definitions import DEFAULT_SETTING_DEFINITIONS
from app.infrastructure.database.models import AppSettingDefinitionModel, UserModel


@pytest.fixture
async def admin_user(test_session: AsyncSession) -> UserModel:
    user = UserModel(
        id="admin-settings-id",
        username="settingsadmin",
        email="settingsadmin@example.com",
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
        json={"username": "settingsadmin", "password": "TestPass123"},
    )
    assert response.status_code == 200
    csrf = response.json().get("csrf_token")
    headers = {"X-CSRF-Token": csrf} if csrf else {}
    return client, headers


@pytest.fixture
async def seeded_settings(test_session: AsyncSession) -> None:
    for definition in DEFAULT_SETTING_DEFINITIONS:
        test_session.add(AppSettingDefinitionModel(**definition))
    await test_session.commit()


@pytest.mark.asyncio
async def test_get_settings_requires_auth(client):
    response = await client.get("/api/v1/settings")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_settings_as_admin(admin_client, seeded_settings):
    client, _ = admin_client
    response = await client.get("/api/v1/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(DEFAULT_SETTING_DEFINITIONS)
    assert len(data["categories"]) == 8


@pytest.mark.asyncio
async def test_update_setting(admin_client, seeded_settings):
    client, headers = admin_client
    response = await client.put(
        "/api/v1/settings",
        json={
            "settings": [
                {"category": "upload", "key": "max_upload_size_mb", "value": 75},
            ],
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["updated"] == 1

    get_response = await client.get("/api/v1/settings?category=upload")
    upload_settings = get_response.json()["categories"][0]["settings"]
    size_setting = next(s for s in upload_settings if s["key"] == "max_upload_size_mb")
    assert size_setting["value"] == 75
    assert size_setting["is_modified"] is True


@pytest.mark.asyncio
async def test_export_import_settings(admin_client, seeded_settings):
    client, headers = admin_client

    export_response = await client.get("/api/v1/settings/export")
    assert export_response.status_code == 200
    payload = export_response.json()
    assert "settings" in payload
    assert "upload.max_upload_size_mb" in payload["settings"]

    import_response = await client.post(
        "/api/v1/settings/import",
        json={
            "settings": {"system.application_name": "Custom App Name"},
            "merge": True,
        },
        headers=headers,
    )
    assert import_response.status_code == 200
    assert import_response.json()["imported"] >= 1
