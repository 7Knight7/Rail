"""Unit tests for Report Vande Bharat (Report No. 18) registration."""

from __future__ import annotations

import csv
from pathlib import Path

from app.automation.formatting.artifact_titles import (
    ARTIFACT_DISPLAY_TITLES,
    build_artifact_main_title,
    is_artifact_title_row,
)
from app.automation.handlers.registry import HANDLER_REGISTRY, get_handler
from app.automation.processing.registry import PROCESSORS
from app.automation.processing.report18_processor import Report18Processor
from app.automation.report_keys import CANONICAL_KEYS, is_supported_report_key
from app.automation.report18_filters import REPORT18_FILE_STEM
from app.automation.reports import DEFAULT_CATALOG, REPORT_18, catalog
from app.automation.date_range import ReportDateRange
from datetime import date
from app.features.datasets.service import SUPPORTED_REPORT_IDS
from app.features.reports.slug_map import MANUAL_REPORT_SLUGS, PAGE_ID_TO_SLUG, resolve_manual_slug


class TestReport18Registration:
    def test_report18_in_canonical_keys(self):
        assert "report18" in CANONICAL_KEYS
        assert is_supported_report_key("report18")

    def test_report18_in_default_catalog_last(self):
        slugs = [r.slug for r in DEFAULT_CATALOG]
        assert slugs.count("report18") == 1
        assert slugs[-1] == "report18"
        assert slugs[-2] == "report14"

    def test_catalog_instance_order(self):
        slugs = [r.slug for r in catalog.reports]
        assert slugs[-1] == "report18"
        assert len(slugs) == 10

    def test_handler_registered(self):
        assert "report18" in HANDLER_REGISTRY
        handler = get_handler("report18")
        assert handler.__class__.__name__ == "Report18Handler"

    def test_processor_registered(self):
        assert "report18" in PROCESSORS
        assert isinstance(PROCESSORS["report18"], Report18Processor)

    def test_manual_slug_and_page_id(self):
        assert "report18" in MANUAL_REPORT_SLUGS
        assert PAGE_ID_TO_SLUG["report18"] == "report18"
        assert resolve_manual_slug("report18") == "report18"

    def test_supported_dataset_id(self):
        assert "report18" in SUPPORTED_REPORT_IDS

    def test_portal_definition(self):
        assert REPORT_18.slug == "report18"
        assert REPORT_18.name == "Report Vande Bharat"
        assert "vandebharatreport" in REPORT_18.page_path
        assert REPORT_18.url_fragment == "mis_reports/vandebharatreport"


class TestReport18Processor:
    def test_writes_exact_artifact_names(self, tmp_path: Path):
        csv_path = tmp_path / "vande_bharat.csv"
        with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Train", "Received"])
            writer.writerow(["VB 1", "10"])
            writer.writerow(["VB 2", "5"])

        processor = Report18Processor()
        result = processor.process(
            source_a_path=csv_path,
            report_slug="report18",
            column_selection={"run_id": "run-test"},
        )
        assert result.success
        assert result.excel_path
        assert result.pdf_path
        assert Path(result.excel_path).name == f"{REPORT18_FILE_STEM}.xlsx"
        assert Path(result.pdf_path).name == f"{REPORT18_FILE_STEM}.pdf"
        assert Path(result.excel_path).is_file()
        assert Path(result.pdf_path).is_file()

    def test_fails_on_empty_table(self, tmp_path: Path):
        csv_path = tmp_path / "empty.csv"
        with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Train", "Received"])

        result = Report18Processor().process(
            source_a_path=csv_path,
            report_slug="report18",
            column_selection={"run_id": "run-empty"},
        )
        assert not result.success
        assert "REPORT18_TABLE_MISSING" in (result.error or "")


class TestReport18Titles:
    def test_artifact_display_title(self):
        assert ARTIFACT_DISPLAY_TITLES["report18"] == "Report Vande Bharat"

    def test_build_title_includes_date(self):
        dr = ReportDateRange(date_from=date(2026, 8, 4), date_to=date(2026, 8, 4))
        title = build_artifact_main_title("report18", dr)
        assert title.startswith("Report Vande Bharat")
        assert is_artifact_title_row([title])
