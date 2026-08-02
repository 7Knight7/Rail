"""Tests for Report 10-13 comprehensive column configuration."""

from __future__ import annotations

import pytest

from app.automation.comprehensive1013_filters import COMPREHENSIVE_1013_SECTION_IDS
from app.automation.processing.column_config import (
    comprehensive_union_column_keys,
    sanitize_comprehensive_sections,
    validate_comprehensive_sections,
)
from app.automation.processing.comprehensive1013_processor import Comprehensive1013Processor
from app.features.reports.schemas import ManualGenerateRequest
from app.features.reports.service import build_config_snapshot


def _full_sections(**overrides: list[str]) -> dict[str, dict[str, list[str]]]:
    defaults = {
        section_id: {
            "selected_column_ids": [
                "sno",
                "division",
                "opening_balance",
                "received",
                "share_percent",
                "closed",
                "closing_balance",
                "disposal_percent",
                "avg_disposal_time",
                "avg_rating",
                "avg_pendency_time",
            ]
        }
        for section_id in COMPREHENSIVE_1013_SECTION_IDS
    }
    for section_id, selected in overrides.items():
        defaults[section_id] = {"selected_column_ids": selected}
    return defaults


def test_build_config_snapshot_writes_top_level_sections_and_dates():
    sections = _full_sections(
        report10_cw=["sno", "division", "received", "closed"],
        report11_security=["sno", "division", "received", "share_percent", "avg_rating"],
    )
    body = ManualGenerateRequest(
        date_from="2026-08-01",
        date_to="2026-08-02",
        sections=sections,
    )
    snapshot = build_config_snapshot(body, report_slug="comprehensive-10-13")

    assert snapshot["date_from"] == "2026-08-01"
    assert snapshot["date_to"] == "2026-08-02"
    assert snapshot["sections"]["report10_cw"]["selected_column_ids"] == [
        "sno",
        "division",
        "received",
        "closed",
    ]
    assert snapshot["sections"]["report11_security"]["selected_column_ids"] == [
        "sno",
        "division",
        "received",
        "share_percent",
        "avg_rating",
    ]
    assert "opening_balance" in comprehensive_union_column_keys(snapshot["sections"])


def test_validate_comprehensive_sections_requires_each_section():
    with pytest.raises(ValueError, match="Report 10 — C&W"):
        validate_comprehensive_sections(
            {
                "report10_cw": {"selected_column_ids": []},
                "report11_security": {"selected_column_ids": ["sno"]},
                "report12_punctuality": {"selected_column_ids": ["sno"]},
                "report13_electrical": {"selected_column_ids": ["sno"]},
            }
        )


def test_sanitize_comprehensive_sections_filters_invalid_ids():
    sections = _full_sections(
        report10_cw=["sno", "division", "invalid_column", "received"],
    )
    sanitized = sanitize_comprehensive_sections(sections)
    assert sanitized["report10_cw"]["selected_column_ids"] == [
        "sno",
        "division",
        "received",
    ]


def test_resolve_column_ids_uses_section_specific_selection():
    processor = Comprehensive1013Processor()
    column_selection = {
        "sections": _full_sections(
            report10_cw=["sno", "division", "received", "closed"],
            report11_security=["sno", "division", "received"],
        )
    }

    report10_cols = processor._resolve_column_ids("report10_cw", column_selection)
    report11_cols = processor._resolve_column_ids("report11_security", column_selection)

    assert report10_cols == ["sno", "division", "received", "closed"]
    assert report11_cols == ["sno", "division", "received"]
    assert "opening_balance" not in report10_cols
    assert "opening_balance" in processor._resolve_column_ids(
        "report12_punctuality", column_selection
    )


def test_resolve_column_ids_errors_when_sections_present_but_section_empty():
    processor = Comprehensive1013Processor()
    column_selection = {
        "sections": {
            "report10_cw": {"selected_column_ids": ["sno", "division"]},
            "report11_security": {"selected_column_ids": []},
            "report12_punctuality": {"selected_column_ids": ["division"]},
            "report13_electrical": {"selected_column_ids": ["division"]},
        }
    }

    with pytest.raises(ValueError, match="Report 11 — Security"):
        processor._resolve_column_ids("report11_security", column_selection)


def test_project_columns_omits_deselected_fields():
    processor = Comprehensive1013Processor()
    raw_headers = [
        "S.No.",
        "Division",
        "Opening Balance",
        "Received",
        "Closed",
    ]
    data_rows = [
        {
            "S.No.": "1",
            "Division": "Hyderabad",
            "Opening Balance": "10",
            "Received": "5",
            "Closed": "3",
        }
    ]
    headers, rows = processor._project_columns(
        raw_headers,
        data_rows,
        ["sno", "division", "received", "closed"],
    )

    assert headers == ["S.No.", "Division", "Received", "Closed"]
    assert rows == [["1", "Hyderabad", "5", "3"]]
