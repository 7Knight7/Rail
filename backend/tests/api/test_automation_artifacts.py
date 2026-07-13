"""Tests for CDP run artifact preview/download APIs."""

from __future__ import annotations

import io
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.automation.config import config
from app.automation.dependencies import get_automation_service
from app.automation.run_registry import (
    ArtifactPathError,
    create_cdp_run,
    ensure_cdp_profile,
    register_artifact,
    validate_artifact_file,
)
from app.domain.entities.user import User, UserRole
from app.features.auth.dependencies import require_admin, validate_csrf_token
from app.infrastructure.database.session import get_db_session
from app.main import app
from unittest.mock import AsyncMock


@pytest.fixture
def admin_user() -> User:
    now = datetime.now(UTC)
    return User(
        id="test-admin",
        username="admin",
        email="admin@test.local",
        password_hash="hash",
        role=UserRole.ADMIN,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
async def api_client(admin_user: User, test_session: AsyncSession):
    async def override_admin() -> User:
        return admin_user

    def override_csrf() -> None:
        return None

    async def override_db():
        yield test_session

    app.dependency_overrides[get_automation_service] = lambda: AsyncMock()
    app.dependency_overrides[require_admin] = override_admin
    app.dependency_overrides[validate_csrf_token] = override_csrf
    app.dependency_overrides[get_db_session] = override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


def test_validate_artifact_blocks_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "output_pdf_dir", str(tmp_path / "pdf"))
    monkeypatch.setattr(config, "output_excel_dir", str(tmp_path / "excel"))
    monkeypatch.setattr(config, "extracted_data_dir", str(tmp_path / "extracted"))
    monkeypatch.setattr(config, "pdf_archive_dir", str(tmp_path / "archive"))
    (tmp_path / "pdf").mkdir()
    evil = Path(tmp_path / "outside" / "secret.pdf")
    evil.parent.mkdir(parents=True)
    evil.write_bytes(b"%PDF-1.4x")
    with pytest.raises(ArtifactPathError):
        validate_artifact_file(evil)


@pytest.mark.asyncio
async def test_artifact_preview_download_and_zip(
    tmp_path, monkeypatch, api_client, test_session: AsyncSession
):
    pdf_dir = tmp_path / "pdf" / "division"
    excel_dir = tmp_path / "excel" / "division"
    pdf_dir.mkdir(parents=True)
    excel_dir.mkdir(parents=True)
    pdf_path = pdf_dir / "sample.pdf"
    excel_path = excel_dir / "sample.xlsx"
    pdf_path.write_bytes(b"%PDF-1.4 sample")
    excel_path.write_bytes(b"PK\x03\x04excel")

    monkeypatch.setattr(config, "output_pdf_dir", str(tmp_path / "pdf"))
    monkeypatch.setattr(config, "output_excel_dir", str(tmp_path / "excel"))
    monkeypatch.setattr(config, "extracted_data_dir", str(tmp_path / "extracted"))
    monkeypatch.setattr(config, "pdf_archive_dir", str(tmp_path / "archive"))
    (tmp_path / "extracted").mkdir(exist_ok=True)
    (tmp_path / "archive").mkdir(exist_ok=True)

    await ensure_cdp_profile(test_session)
    run = await create_cdp_run(test_session)
    pdf_art = await register_artifact(
        test_session,
        run_id=run.id,
        report_slug="division",
        report_name="division",
        file_type="pdf",
        file_path=pdf_path,
    )
    excel_art = await register_artifact(
        test_session,
        run_id=run.id,
        report_slug="division",
        report_name="division",
        file_type="excel",
        file_path=excel_path,
    )

    preview = await api_client.get(f"/api/v1/automation/artifacts/{pdf_art.id}/preview")
    assert preview.status_code == 200
    assert "inline" in preview.headers.get("content-disposition", "")
    assert preview.content.startswith(b"%PDF-")

    download = await api_client.get(f"/api/v1/automation/artifacts/{pdf_art.id}/download")
    assert download.status_code == 200
    assert "attachment" in download.headers.get("content-disposition", "")

    excel_dl = await api_client.get(
        f"/api/v1/automation/artifacts/{excel_art.id}/download"
    )
    assert excel_dl.status_code == 200

    run_resp = await api_client.get(f"/api/v1/automation/runs/{run.id}")
    assert run_resp.status_code == 200
    assert run_resp.json()["run_id"] == run.id

    arts = await api_client.get(f"/api/v1/automation/runs/{run.id}/artifacts")
    assert arts.status_code == 200
    assert len(arts.json()) == 2
    assert all("file_path" not in a for a in arts.json())

    zipped = await api_client.get(f"/api/v1/automation/runs/{run.id}/download-all")
    assert zipped.status_code == 200
    assert zipped.headers["content-type"].startswith("application/zip")
    with zipfile.ZipFile(io.BytesIO(zipped.content)) as zf:
        names = zf.namelist()
        assert any(n.endswith(".pdf") for n in names)
        assert any(n.endswith(".xlsx") for n in names)


@pytest.mark.asyncio
async def test_missing_artifact_returns_404(api_client):
    resp = await api_client.get(f"/api/v1/automation/artifacts/{uuid4()}/download")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_run_detail_scrubs_filesystem_paths(
    tmp_path, monkeypatch, api_client, test_session: AsyncSession
):
    from app.automation.schemas import MultiReportResult, ReportResult
    from app.automation.run_registry import finalize_cdp_run

    monkeypatch.setattr(config, "output_pdf_dir", str(tmp_path / "pdf"))
    monkeypatch.setattr(config, "output_excel_dir", str(tmp_path / "excel"))
    monkeypatch.setattr(config, "extracted_data_dir", str(tmp_path / "extracted"))
    monkeypatch.setattr(config, "pdf_archive_dir", str(tmp_path / "archive"))
    for name in ("pdf", "excel", "extracted", "archive"):
        (tmp_path / name).mkdir(exist_ok=True)

    run = await create_cdp_run(test_session)
    result = MultiReportResult(
        success=True,
        connected=True,
        tab_found=True,
        run_id=run.id,
        reports=[
            ReportResult(
                slug="division",
                dataset_key="division",
                status="success",
                excel_path=str(tmp_path / "excel" / "x.xlsx"),
                pdf_path=str(tmp_path / "pdf" / "x.pdf"),
                source_csv_path=str(tmp_path / "extracted" / "x.csv"),
                source_paths=[str(tmp_path / "extracted" / "x.csv")],
                archive_path=str(tmp_path / "archive" / "x.pdf"),
                pdf_download_url="/api/v1/automation/artifacts/a/download",
                pdf_preview_url="/api/v1/automation/artifacts/a/preview",
            )
        ],
    )
    await finalize_cdp_run(test_session, run.id, result)

    resp = await api_client.get(f"/api/v1/automation/runs/{run.id}")
    assert resp.status_code == 200
    body = resp.json()
    report = body["reports"][0]
    assert "excel_path" not in report
    assert "pdf_path" not in report
    assert "source_csv_path" not in report
    assert "source_paths" not in report
    assert "archive_path" not in report
    assert report["pdf_download_url"].endswith("/download")


@pytest.mark.asyncio
async def test_start_accepts_report_slugs_subset(api_client, admin_user):
    mock_service = AsyncMock()
    from app.automation.schemas import MultiReportResult

    mock_service.start = AsyncMock(
        return_value=MultiReportResult(
            success=True,
            connected=True,
            tab_found=True,
            run_id="run-subset",
            reports=[],
        )
    )
    app.dependency_overrides[get_automation_service] = lambda: mock_service

    resp = await api_client.post(
        "/api/v1/automation/start",
        json={"report_slugs": ["division"]},
    )
    assert resp.status_code == 200
    mock_service.start.assert_awaited()
    kwargs = mock_service.start.await_args.kwargs
    assert kwargs.get("report_slugs") == ["division"]
    assert kwargs.get("user_id") == admin_user.id
