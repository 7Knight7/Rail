"""Unit tests for automation configuration."""

import pytest
from pydantic import ValidationError

from app.automation.config import AutomationConfig


def test_defaults(monkeypatch: pytest.MonkeyPatch):
    for key in ("CHROME_DEBUG_URL", "DOWNLOAD_FOLDER", "TIMEOUT", "RETRY_COUNT", "RAILMADAD_URL"):
        monkeypatch.delenv(key, raising=False)

    cfg = AutomationConfig(_env_file=None)
    assert cfg.chrome_debug_url == "http://127.0.0.1:9222"
    assert cfg.download_folder == "downloads"
    assert cfg.timeout == 300
    assert cfg.retry_count == 3
    assert cfg.railmadad_url == "https://railmadad.indianrail.gov.in"


def test_reads_from_environment(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("CHROME_DEBUG_URL", "http://127.0.0.1:9333")
    monkeypatch.setenv("DOWNLOAD_FOLDER", "/tmp/reports")
    monkeypatch.setenv("TIMEOUT", "120")
    monkeypatch.setenv("RETRY_COUNT", "5")
    monkeypatch.setenv("RAILMADAD_URL", "https://example.test/portal")

    cfg = AutomationConfig(_env_file=None)

    assert cfg.chrome_debug_url == "http://127.0.0.1:9333"
    assert cfg.download_folder == "/tmp/reports"
    assert cfg.timeout == 120
    assert cfg.retry_count == 5
    assert cfg.railmadad_url == "https://example.test/portal"


def test_timeout_must_be_positive():
    with pytest.raises(ValidationError):
        AutomationConfig(timeout=0)


def test_retry_count_cannot_be_negative():
    with pytest.raises(ValidationError):
        AutomationConfig(retry_count=-1)
