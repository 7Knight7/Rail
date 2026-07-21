"""Unit tests for Microsoft Edge executable resolution."""

from pathlib import Path

import importlib

import pytest

from app.automation.config import resolve_edge_executable

_config_module = importlib.import_module("app.automation.config")


def test_resolve_edge_executable_env_override(tmp_path: Path):
    fake_edge = tmp_path / "msedge.exe"
    fake_edge.write_text("stub", encoding="utf-8")

    resolved = resolve_edge_executable(str(fake_edge))

    assert resolved == fake_edge


def test_resolve_edge_executable_prefers_x86_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    x86 = tmp_path / "x86" / "Microsoft" / "Edge" / "Application"
    x64 = tmp_path / "x64" / "Microsoft" / "Edge" / "Application"
    x86.mkdir(parents=True)
    x64.mkdir(parents=True)
    x86_edge = x86 / "msedge.exe"
    x64_edge = x64 / "msedge.exe"
    x86_edge.write_text("x86", encoding="utf-8")
    x64_edge.write_text("x64", encoding="utf-8")

    monkeypatch.setattr(
        _config_module,
        "EDGE_EXECUTABLE_CANDIDATES",
        (x86_edge, x64_edge),
    )

    assert resolve_edge_executable(None) == x86_edge


def test_resolve_edge_executable_falls_back_to_x64(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    x64 = tmp_path / "x64" / "Microsoft" / "Edge" / "Application"
    x64.mkdir(parents=True)
    x64_edge = x64 / "msedge.exe"
    x64_edge.write_text("x64", encoding="utf-8")
    missing_x86 = tmp_path / "x86" / "Microsoft" / "Edge" / "Application" / "msedge.exe"

    monkeypatch.setattr(
        _config_module,
        "EDGE_EXECUTABLE_CANDIDATES",
        (missing_x86, x64_edge),
    )

    assert resolve_edge_executable(None) == x64_edge


def test_resolve_edge_executable_returns_none_when_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    missing = tmp_path / "missing" / "msedge.exe"
    monkeypatch.setattr(_config_module, "EDGE_EXECUTABLE_CANDIDATES", (missing,))

    assert resolve_edge_executable(None) is None
