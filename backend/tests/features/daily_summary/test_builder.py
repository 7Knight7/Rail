"""Unit tests for Daily Summary builders and source isolation."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from app.features.daily_summary.builder import (
    build_full_summary,
    build_report3_section,
    build_report4_section,
    build_report5_section,
    build_report6_section,
)
from app.features.daily_summary.sources import ReportSource, RunSources


def _write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def test_report3_no_scr_sentence():
    rows = [
        {
            "Train No.": "12345",
            "Train Name": "OTHER EXP",
            "Owning Zone": "Northern Railway",
            "Owning Division": "DLI",
            "Received": "10",
        }
    ]
    source = ReportSource(slug="train-no", status="success", available=True, rows=rows)
    text, _ = build_report3_section(source, "14.07.2026")
    assert "No SCR based train had come as on 14.07.2026" in text
    assert "Bottom 20 trains w.r.to maximum Grievances" in text


def test_report3_lists_scr_trains():
    rows = [
        {
            "Train No.": "12721",
            "Train Name": "DAKSHIN",
            "Owning Zone": "South Central Railway",
            "Owning Division": "SC",
            "Received": "42",
        },
        {
            "Train No.": "99999",
            "Train Name": "OTHER",
            "Owning Zone": "Western Railway",
            "Owning Division": "BCT",
            "Received": "40",
        },
    ]
    source = ReportSource(slug="train-no", status="success", available=True, rows=rows)
    text, count = build_report3_section(source, "14.07.2026")
    assert "12721 DAKSHIN with 42 complaints" in text
    assert "99999" not in text
    assert count == 2


def test_report4_groups_by_type_and_division():
    source = ReportSource(
        slug="types",
        status="success",
        available=True,
        type_datasets={
            "Security": [
                {
                    "Train No.": "12721",
                    "Train Name": "DAKSHIN",
                    "Owning Zone": "South Central Railway",
                    "Owning Division": "HYB",
                    "Received": "5",
                }
            ],
            "Bedroll": [
                {
                    "Train No.": "17001",
                    "Train Name": "EXP",
                    "Owning Zone": "Western Railway",
                    "Owning Division": "BCT",
                    "Received": "9",
                }
            ],
        },
    )
    text, _ = build_report4_section(source, "14.07.2026")
    assert "Security" in text
    assert "HYB" in text
    assert "12721 DAKSHIN 5 complaints" in text
    assert "Bedroll" not in text  # no SCR rows


def test_report5_totals_and_groups():
    source = ReportSource(
        slug="scr-train",
        status="success",
        available=True,
        row_counts={"expected": 3, "unsatisfactory": 3, "unsatisfactory_percent": 40.0},
        rows=[
            {"Type": "Coach - Cleanliness", "Div": "HYB", "Mode": "T"},
            {"Type": "Coach - Cleanliness", "Div": "SC", "Mode": "T"},
            {"Type": "Security", "Div": "HYB", "Mode": "T"},
        ],
    )
    text, count, notes = build_report5_section(source, "14.07.2026")
    assert "Total unsatisfactory feed-back of trains are 3, 40.00%" in text
    assert "Coach - Cleanliness    2" in text
    assert "Security    1" in text
    assert "DIVISION Wise" in text
    assert "HYB 2" in text
    assert count == 3
    assert notes == []


def test_report5_zero_state():
    source = ReportSource(
        slug="scr-train",
        status="success",
        available=True,
        row_counts={"expected": 0, "unsatisfactory": 0},
        rows=[],
    )
    text, _, _ = build_report5_section(source, "14.07.2026")
    assert "Total unsatisfactory feed-back of trains are 0." in text
    assert "No unsatisfactory train feedback cases were reported as on 14.07.2026." in text


def test_report6_formats_and_excludes_pii():
    source = ReportSource(
        slug="scr-station",
        status="success",
        available=True,
        row_counts={"expected": 1},
        rows=[
            {
                "Train/Station": "BMT",
                "complaintDesc": "Platform dirty near entrance",
                "Dept": "CML",
                "Div": "HYB",
                "userMobile": "9999999999",
                "contactId": "secret",
                "userId": "u1",
            }
        ],
    )
    text, _ = build_report6_section(source, "14.07.2026")
    assert "Unsatisfactory feedback at station are 1" in text
    assert "BMT" in text
    assert "Platform dirty near entrance" in text
    assert "[CML-HYB]" in text
    assert "9999999999" not in text
    assert "secret" not in text
    assert "u1" not in text


def test_report6_zero_state():
    source = ReportSource(
        slug="scr-station",
        status="success",
        available=True,
        row_counts={"expected": 0},
        rows=[],
    )
    text, _ = build_report6_section(source, "14.07.2026")
    assert "Unsatisfactory feedback at station are 0." in text


def test_full_summary_marks_missing_sections(tmp_path: Path, monkeypatch):
    sources = RunSources(
        run_id="run-1",
        user_id="user-1",
        run_status="completed",
        reports={
            "train-no": ReportSource(
                slug="train-no",
                status="success",
                available=True,
                rows=[
                    {
                        "Train No.": "1",
                        "Train Name": "X",
                        "Owning Zone": "Northern Railway",
                        "Received": "1",
                    }
                ],
            ),
        },
        missing_reports=["types", "scr-train", "scr-station"],
        all_terminal=True,
    )
    text, counts, missing, _ = build_full_summary(sources, "14.07.2026")
    assert "No SCR based train" in text
    assert "Report 4 unavailable" in text
    assert "Report 5 unavailable" in text
    assert "Report 6 unavailable" in text
    assert "types" in missing
    assert counts["train-no"] == 1


def test_resolve_run_sources_uses_result_json_only(tmp_path, monkeypatch):
    from app.features.daily_summary.sources import resolve_run_sources
    from app.infrastructure.database.models import AutomationRunModel

    storage = tmp_path / "storage" / "extracted" / "train-no"
    storage.mkdir(parents=True)
    current = storage / "current.csv"
    stale = storage / "stale.csv"
    _write_csv(
        current,
        ["Train No.", "Train Name", "Owning Zone", "Owning Division", "Received"],
        [["12721", "DAKSHIN", "South Central Railway", "SC", "5"]],
    )
    _write_csv(
        stale,
        ["Train No.", "Train Name", "Owning Zone", "Owning Division", "Received"],
        [["99999", "STALE", "South Central Railway", "SC", "99"]],
    )

    monkeypatch.setattr(
        "app.features.daily_summary.sources.is_under_storage",
        lambda p: True,
    )

    run = AutomationRunModel(
        id="run-abc",
        profile_id="prof",
        status="completed",
        created_by="user-1",
        result_json=json.dumps(
            {
                "reports": [
                    {
                        "slug": "train-no",
                        "status": "success",
                        "source_csv_path": str(current),
                        "source_paths": [str(current)],
                        "row_counts": {},
                    }
                ]
            }
        ),
    )
    sources = resolve_run_sources(run)
    assert sources.reports["train-no"].available
    assert sources.reports["train-no"].rows[0]["Train No."] == "12721"
    assert all(r["Train No."] != "99999" for r in sources.reports["train-no"].rows)
