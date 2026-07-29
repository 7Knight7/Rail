"""Focused PDF layout tests for Report 10-13 (single page, section order)."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table

from app.automation.comprehensive1013_filters import COMPREHENSIVE_1013_SECTION_IDS
from app.automation.processing.comprehensive1013_processor import Comprehensive1013Processor
from app.automation.processing.comprehensive_output_columns import COMPREHENSIVE_COLUMN_LABELS

SECTION_HEADING_MARKERS = [
    "C&W complaints division wise",
    "Security complaints",
    "Punctuality complaints",
    "Electrical Equipment complaints division wise",
]


def _count_pdf_pages(pdf_path: Path) -> int:
    raw = pdf_path.read_bytes().decode("latin-1", errors="ignore")
    return raw.count("/Type /Page") - raw.count("/Type /Pages")


def _paragraph_from_table_cell(cell: object) -> Paragraph | None:
    if isinstance(cell, Paragraph):
        return cell
    if isinstance(cell, tuple) and cell and isinstance(cell[0], Paragraph):
        return cell[0]
    return None


def _paragraph_text(paragraph: Paragraph) -> str:
    return str(getattr(paragraph, "text", "") or getattr(paragraph, "plainText", "") or "")


def _write_section_csv(path: Path, *, division: str, received: int) -> None:
    headers = list(COMPREHENSIVE_COLUMN_LABELS.values())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerow(
            {
                "S.No.": "1",
                "Division": division,
                "Opening Balance": "0",
                "Received": str(received),
                "% Share": "100.00",
                "Closed": str(received),
                "Closing Balance": "0",
                "% Disposal": "100.00",
                "Avg. Disposal Time": "1.0",
                "Avg. Rating": "4.0",
                "Avg. Pendency Time": "0.0",
            }
        )
        writer.writerow(
            {
                "S.No.": "",
                "Division": "Total",
                "Opening Balance": "0",
                "Received": str(received),
                "% Share": "100.00",
                "Closed": str(received),
                "Closing Balance": "0",
                "% Disposal": "100.00",
                "Avg. Disposal Time": "1.0",
                "Avg. Rating": "4.0",
                "Avg. Pendency Time": "0.0",
            }
        )


def _write_combined_index(base_dir: Path) -> Path:
    index_path = base_dir / "comprehensive_combined_index.csv"
    with index_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["section_id", "section_name", "csv_path", "row_count", "status", "error"],
        )
        writer.writeheader()
        samples = {
            "report10_cw": ("SC", 3),
            "report11_security": ("HYB", 5),
            "report12_punctuality": ("BZA", 7),
            "report13_electrical": ("GNT", 9),
        }
        for section_id in COMPREHENSIVE_1013_SECTION_IDS:
            division, received = samples[section_id]
            csv_path = base_dir / f"{section_id}.csv"
            _write_section_csv(csv_path, division=division, received=received)
            writer.writerow(
                {
                    "section_id": section_id,
                    "section_name": section_id,
                    "csv_path": str(csv_path),
                    "row_count": "1",
                    "status": "success",
                    "error": "",
                }
            )
    return index_path


def test_comprehensive1013_pdf_is_single_page_with_section_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    extracted = tmp_path / "extracted" / "comprehensive-10-13"
    excel_dir = tmp_path / "output" / "excel"
    pdf_dir = tmp_path / "output" / "pdf"
    extracted.mkdir(parents=True)
    excel_dir.mkdir(parents=True)
    pdf_dir.mkdir(parents=True)

    monkeypatch.setattr(
        "app.automation.processing.comprehensive1013_processor.config.extracted_data_dir",
        str(tmp_path / "extracted"),
    )
    monkeypatch.setattr(
        "app.automation.processing.comprehensive1013_processor.config.output_excel_dir",
        str(excel_dir),
    )
    monkeypatch.setattr(
        "app.automation.processing.comprehensive1013_processor.config.output_pdf_dir",
        str(pdf_dir),
    )

    captured: dict[str, object] = {}
    original_build = SimpleDocTemplate.build

    def _capture_build(self, flowables, *args, **kwargs):  # noqa: ANN001
        captured["flowables"] = list(flowables)
        captured["pagesize"] = self.pagesize
        return original_build(self, flowables, *args, **kwargs)

    monkeypatch.setattr(SimpleDocTemplate, "build", _capture_build)

    index_path = _write_combined_index(extracted)
    result = Comprehensive1013Processor().process(
        source_a_path=index_path,
        report_slug="comprehensive-10-13",
        column_selection={"date_from": "2026-07-29", "date_to": "2026-07-29"},
    )

    assert result.success is True, result.error
    assert result.pdf_path
    assert result.excel_path
    pdf_path = Path(result.pdf_path)
    excel_path = Path(result.excel_path)
    assert pdf_path.is_file()
    assert excel_path.is_file()

    assert _count_pdf_pages(pdf_path) == 1

    flowables = captured["flowables"]
    assert flowables is not None
    assert not any(isinstance(item, PageBreak) for item in flowables)

    paragraph_texts = [
        _paragraph_text(item)
        for item in flowables
        if isinstance(item, Paragraph)
    ]
    for item in flowables:
        if isinstance(item, Table) and len(item._cellvalues) == 1 and len(item._cellvalues[0]) == 1:
            cell_paragraph = _paragraph_from_table_cell(item._cellvalues[0][0])
            if cell_paragraph is not None:
                paragraph_texts.append(_paragraph_text(cell_paragraph))
    # reportlab may store markup entities; normalize for assertions
    normalized = [text.replace("&amp;", "&") for text in paragraph_texts]

    title_hits = [text for text in normalized if "Report 10-13 (Comprehensive Reports)" in text]
    assert len(title_hits) == 1

    heading_positions: list[int] = []
    for marker in SECTION_HEADING_MARKERS:
        matches = [idx for idx, text in enumerate(normalized) if marker in text]
        assert matches, f"Missing section heading marker: {marker!r} in {normalized!r}"
        heading_positions.append(matches[0])
    assert heading_positions == sorted(heading_positions)

    # Each section heading sits in a 1-row Table whose width matches the data table below it.
    section_tables: list[tuple[Table, Table]] = []
    idx = 0
    while idx < len(flowables) - 2:
        heading_candidate = flowables[idx]
        spacer_candidate = flowables[idx + 1]
        data_candidate = flowables[idx + 2]
        if (
            isinstance(heading_candidate, Table)
            and isinstance(spacer_candidate, Spacer)
            and isinstance(data_candidate, Table)
            and len(heading_candidate._cellvalues) == 1
            and len(heading_candidate._cellvalues[0]) == 1
            and len(data_candidate._cellvalues) > 1
        ):
            section_tables.append((heading_candidate, data_candidate))
            idx += 3
            continue
        idx += 1

    assert len(section_tables) == 4
    for heading_table, data_table in section_tables:
        heading_width = float(sum(heading_table._colWidths))
        data_width = float(sum(data_table._colWidths))
        assert abs(heading_width - data_width) < 0.5
        heading_paragraph = _paragraph_from_table_cell(heading_table._cellvalues[0][0])
        assert heading_paragraph is not None
        assert heading_paragraph.style.alignment == TA_CENTER
        assert float(getattr(heading_paragraph, "width", heading_width)) == pytest.approx(
            heading_width,
            abs=0.5,
        )
