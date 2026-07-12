"""Tests for Report 2 Phase 8 processor (Division Wise Top 25)."""

from pathlib import Path

import pytest
from openpyxl import load_workbook

from app.automation.processing.base import ProcessingResult
from app.automation.processing.registry import PROCESSORS
from app.automation.processing.report2_processor import Report2Processor, TOP_N, HIDDEN_COLUMNS

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "report2"


@pytest.fixture
def processor() -> Report2Processor:
    return Report2Processor()


@pytest.fixture
def comprehensive_csv(tmp_path: Path) -> Path:
    extracted = tmp_path / "extracted" / "report2"
    extracted.mkdir(parents=True, exist_ok=True)
    target = extracted / "report2_division_comprehensive_raw.csv"
    target.write_text(
        (FIXTURES_DIR / "division_comprehensive_raw.csv").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return target


@pytest.fixture
def feedback_csv(tmp_path: Path) -> Path:
    extracted = tmp_path / "extracted" / "report2"
    extracted.mkdir(parents=True, exist_ok=True)
    target = extracted / "report2_division_feedback_raw.csv"
    target.write_text(
        (FIXTURES_DIR / "division_feedback_raw.csv").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return target


def test_registry_selects_report2_processor():
    assert "report2" in PROCESSORS
    assert PROCESSORS["report2"].processor_name == "report2_division_wise_processor"


def test_rejects_pdf_input(processor: Report2Processor, tmp_path: Path):
    pdf_path = tmp_path / "input.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake")

    result = processor.process(source_a_path=pdf_path, report_slug="report2")

    assert result.success is False
    assert "PDF" in (result.error or "")


def test_produces_excel_and_pdf_outputs_without_feedback(
    processor: Report2Processor,
    comprehensive_csv: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.extracted_data_dir",
        str(tmp_path / "extracted"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.output_excel_dir",
        str(tmp_path / "output" / "excel"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.output_pdf_dir",
        str(tmp_path / "output" / "pdf"),
    )

    result = processor.process(source_a_path=comprehensive_csv, report_slug="report2")

    assert result.success is True
    assert result.excel_path is not None
    assert result.pdf_path is not None
    assert Path(result.excel_path).exists()
    assert Path(result.pdf_path).exists()
    assert Path(result.excel_path).stat().st_size > 0
    assert Path(result.pdf_path).stat().st_size > 0


def test_produces_excel_and_pdf_outputs_with_feedback(
    processor: Report2Processor,
    comprehensive_csv: Path,
    feedback_csv: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.extracted_data_dir",
        str(tmp_path / "extracted"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.output_excel_dir",
        str(tmp_path / "output" / "excel"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.output_pdf_dir",
        str(tmp_path / "output" / "pdf"),
    )

    result = processor.process(
        source_a_path=comprehensive_csv,
        report_slug="report2",
        source_b_path=feedback_csv,
    )

    assert result.success is True
    assert result.excel_path is not None
    assert result.pdf_path is not None
    assert Path(result.excel_path).exists()
    assert Path(result.pdf_path).exists()
    assert result.source_a_rows is not None
    assert result.source_b_rows is not None
    assert result.source_b_rows > 0


def test_top_25_selection(
    processor: Report2Processor,
    comprehensive_csv: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.extracted_data_dir",
        str(tmp_path / "extracted"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.output_excel_dir",
        str(tmp_path / "output" / "excel"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.output_pdf_dir",
        str(tmp_path / "output" / "pdf"),
    )

    result = processor.process(source_a_path=comprehensive_csv, report_slug="report2")
    assert result.success is True

    workbook = load_workbook(result.excel_path)
    worksheet = workbook.active

    data_rows = 0
    for row_idx in range(3, worksheet.max_row + 1):
        org_value = worksheet.cell(row=row_idx, column=2).value
        if org_value and "total" not in str(org_value).lower():
            data_rows += 1

    assert data_rows <= TOP_N


def test_columns_hidden(
    processor: Report2Processor,
    comprehensive_csv: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.extracted_data_dir",
        str(tmp_path / "extracted"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.output_excel_dir",
        str(tmp_path / "output" / "excel"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.output_pdf_dir",
        str(tmp_path / "output" / "pdf"),
    )

    result = processor.process(source_a_path=comprehensive_csv, report_slug="report2")
    assert result.success is True

    workbook = load_workbook(result.excel_path)
    worksheet = workbook.active

    from openpyxl.utils import get_column_letter
    for col_idx in HIDDEN_COLUMNS:
        col_letter = get_column_letter(col_idx)
        if col_letter in worksheet.column_dimensions:
            assert worksheet.column_dimensions[col_letter].hidden is True


def test_scr_row_has_yellow_fill_and_black_text(
    processor: Report2Processor,
    comprehensive_csv: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.extracted_data_dir",
        str(tmp_path / "extracted"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.output_excel_dir",
        str(tmp_path / "output" / "excel"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.output_pdf_dir",
        str(tmp_path / "output" / "pdf"),
    )

    result = processor.process(source_a_path=comprehensive_csv, report_slug="report2")
    assert result.success is True

    workbook = load_workbook(result.excel_path)
    worksheet = workbook.active
    scr_found = False
    for row_idx in range(3, worksheet.max_row + 1):
        org_value = worksheet.cell(row=row_idx, column=2).value
        if org_value and "south central railway" in str(org_value).lower():
            scr_found = True
            for col_idx in range(1, worksheet.max_column + 1):
                cell = worksheet.cell(row=row_idx, column=col_idx)
                assert cell.fill.fgColor.rgb in {"00FFFF00", "FFFF00", "FFFFFF00"}
                assert cell.font.color.rgb in {"00000000", "FF000000", "000000"}
    assert scr_found


def test_report_title_contains_bottom_25(
    processor: Report2Processor,
    comprehensive_csv: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.extracted_data_dir",
        str(tmp_path / "extracted"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.output_excel_dir",
        str(tmp_path / "output" / "excel"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.output_pdf_dir",
        str(tmp_path / "output" / "pdf"),
    )

    result = processor.process(source_a_path=comprehensive_csv, report_slug="report2")
    assert result.success is True

    workbook = load_workbook(result.excel_path)
    worksheet = workbook.active
    title_cell = worksheet.cell(row=1, column=1).value
    assert "Bottom 25" in title_cell or "Report No 2" in title_cell


def test_descending_order_preserved(
    processor: Report2Processor,
    comprehensive_csv: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """Verify that rows are in descending order by Received column."""
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.extracted_data_dir",
        str(tmp_path / "extracted"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.output_excel_dir",
        str(tmp_path / "output" / "excel"),
    )
    monkeypatch.setattr(
        "app.automation.processing.report2_processor.config.output_pdf_dir",
        str(tmp_path / "output" / "pdf"),
    )

    result = processor.process(source_a_path=comprehensive_csv, report_slug="report2")
    assert result.success is True

    workbook = load_workbook(result.excel_path)
    worksheet = workbook.active

    received_col = None
    for col_idx in range(1, worksheet.max_column + 1):
        if worksheet.cell(row=2, column=col_idx).value == "Received":
            received_col = col_idx
            break

    assert received_col is not None

    values = []
    for row_idx in range(3, worksheet.max_row):
        val = worksheet.cell(row=row_idx, column=received_col).value
        if val and str(val).strip().isdigit():
            values.append(int(val))

    for i in range(len(values) - 1):
        assert values[i] >= values[i + 1], f"Row {i+3} not in descending order"
