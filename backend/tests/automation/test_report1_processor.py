"""Tests for Report 1 Phase 8 processor."""

from pathlib import Path

import pytest
from openpyxl import load_workbook

from app.automation.processing.base import ProcessingResult
from app.automation.processing.registry import REPORT1_PROCESSOR_NAME, PROCESSORS
from app.automation.processing.report1_processor import Report1Processor

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "report1"


@pytest.fixture
def processor() -> Report1Processor:
    return Report1Processor()


@pytest.fixture
def comprehensive_csv(tmp_path: Path) -> Path:
    extracted = tmp_path / "extracted" / "report1"
    extracted.mkdir(parents=True, exist_ok=True)
    target = extracted / "report1_comprehensive_zone_raw.csv"
    target.write_text(
        (FIXTURES_DIR / "comprehensive_zone_raw.csv").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return target


@pytest.fixture
def feedback_csv(tmp_path: Path) -> Path:
    extracted = tmp_path / "extracted" / "report1"
    extracted.mkdir(parents=True, exist_ok=True)
    target = extracted / "report1_feedback_zone_raw.csv"
    target.write_text(
        (FIXTURES_DIR / "feedback_zone_raw.csv").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return target


def test_registry_selects_report1_processor():
    assert "report1" in PROCESSORS
    assert PROCESSORS["report1"].processor_name == REPORT1_PROCESSOR_NAME


def test_rejects_pdf_input(processor: Report1Processor, tmp_path: Path):
    pdf_path = tmp_path / "input.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    result = processor.process(source_a_path=pdf_path, report_slug="report1")

    assert result.success is False
    assert "PDF" in (result.error or "")


def test_fails_when_feedback_missing(
    processor: Report1Processor,
    comprehensive_csv: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.automation.processing.report1_processor.config.extracted_data_dir",
        str(tmp_path / "extracted"),
    )
    output_excel = tmp_path / "output" / "excel"
    output_pdf = tmp_path / "output" / "pdf"
    monkeypatch.setattr(
        "app.automation.processing.report1_processor.config.output_excel_dir",
        str(output_excel),
    )
    monkeypatch.setattr(
        "app.automation.processing.report1_processor.config.output_pdf_dir",
        str(output_pdf),
    )

    result = processor.process(source_a_path=comprehensive_csv, report_slug="report1")

    assert result.success is False
    assert "Feedback dataset missing" in (result.error or "")
    assert not list(output_excel.rglob("*.xlsx"))


def test_produces_excel_and_pdf_outputs(
    processor: Report1Processor,
    comprehensive_csv: Path,
    feedback_csv: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.automation.processing.report1_processor.config.extracted_data_dir",
        str(tmp_path / "extracted"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report1_processor.config.output_excel_dir",
        str(tmp_path / "output" / "excel"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report1_processor.config.output_pdf_dir",
        str(tmp_path / "output" / "pdf"),
    )

    result = processor.process(source_a_path=comprehensive_csv, report_slug="report1")

    assert result.success is True
    assert result.processor_used is None
    assert result.excel_path is not None
    assert result.pdf_path is not None
    assert Path(result.excel_path).exists()
    assert Path(result.pdf_path).exists()
    assert Path(result.excel_path).stat().st_size > 0
    assert Path(result.pdf_path).stat().st_size > 0
    assert result.source_a_path is not None
    assert result.source_b_path is not None
    assert result.source_a_rows > 0
    assert result.source_b_rows > 0


def test_scr_row_has_yellow_fill_and_black_text(
    processor: Report1Processor,
    comprehensive_csv: Path,
    feedback_csv: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.automation.processing.report1_processor.config.extracted_data_dir",
        str(tmp_path / "extracted"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report1_processor.config.output_excel_dir",
        str(tmp_path / "output" / "excel"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report1_processor.config.output_pdf_dir",
        str(tmp_path / "output" / "pdf"),
    )

    result = processor.process(source_a_path=comprehensive_csv, report_slug="report1")
    assert result.success is True

    workbook = load_workbook(result.excel_path)
    worksheet = workbook.active
    scr_found = False
    for row_idx in range(3, worksheet.max_row + 1):
        org_value = worksheet.cell(row=row_idx, column=2).value
        if org_value and "South Central Railway" in str(org_value):
            scr_found = True
            for col_idx in range(1, worksheet.max_column + 1):
                cell = worksheet.cell(row=row_idx, column=col_idx)
                assert cell.fill.fgColor.rgb in {"00FFFF00", "FFFF00", "FFFFFF00"}
                assert cell.font.color.rgb in {"00000000", "FF000000", "000000"}
    assert scr_found


def test_irctc_alignment(
    processor: Report1Processor,
    comprehensive_csv: Path,
    feedback_csv: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.automation.processing.report1_processor.config.extracted_data_dir",
        str(tmp_path / "extracted"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report1_processor.config.output_excel_dir",
        str(tmp_path / "output" / "excel"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report1_processor.config.output_pdf_dir",
        str(tmp_path / "output" / "pdf"),
    )

    result = processor.process(source_a_path=comprehensive_csv, report_slug="report1")
    assert result.success is True

    workbook = load_workbook(result.excel_path)
    worksheet = workbook.active
    catering_feedback = None
    online_feedback = None
    for row_idx in range(3, worksheet.max_row + 1):
        org_value = str(worksheet.cell(row=row_idx, column=2).value or "")
        feedback_received = worksheet.cell(row=row_idx, column=16).value
        if "Irctc-Catering" in org_value:
            catering_feedback = feedback_received
        if "Irctc-Online" in org_value:
            online_feedback = feedback_received

    assert catering_feedback == "420"
    assert online_feedback in ("", None)
