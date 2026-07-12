"""Report 2 post-ingestion processor (Division Wise Top 25)."""

from __future__ import annotations

import csv
import logging
import re
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.automation.config import config
from app.automation.formatting.scr import highlight_south_central_railway_rows, row_contains_scr
from app.automation.processing.base import ProcessingResult
from app.automation.utils import ensure_directory, log_automation_event, resolve_report_dir

logger = logging.getLogger(__name__)

PROCESSOR_NAME = "report2_division_wise_processor"

TOP_N = 25

FEEDBACK_FILENAME = "report2_division_feedback_raw.csv"
SOURCE_B_DATA_COLUMNS = [
    "Feedback Received",
    "% Feedback",
    "Excellent",
    "Satisfactory",
    "Unsatisfactory",
    "% Unsatisfactory",
]

HIDDEN_COLUMNS = {3, 7, 8, 10, 11, 12, 13, 14, 15}

THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)


class Report2Processor:
    """Process Division Wise Top 25 dataset and emit formatted Excel/PDF."""

    processor_name = PROCESSOR_NAME

    def process(
        self,
        *,
        source_a_path: Path,
        report_slug: str,
        source_b_path: Path | None = None,
    ) -> ProcessingResult:
        if source_a_path.suffix.lower() == ".pdf":
            return ProcessingResult(success=False, error="PDF cannot be used as processing input")

        feedback_path = source_b_path if source_b_path and source_b_path.exists() else None
        if feedback_path is None:
            feedback_path = self._find_feedback_csv(report_slug)

        source_a_rows, source_a_headers = self._read_csv(source_a_path)
        data_a, total_a = self._split_total_row(source_a_rows)

        top_n_rows = data_a[:TOP_N]

        if feedback_path and feedback_path.exists():
            source_b_rows, source_b_headers = self._read_csv(feedback_path)
            data_b, total_b = self._split_total_row(source_b_rows)
            merged_headers = source_a_headers + ["S.No.", "Organisation"] + SOURCE_B_DATA_COLUMNS
            merged_rows = self._merge_rows(top_n_rows, source_a_headers, data_b, source_b_headers)
            if total_a:
                merged_rows.append(self._merge_total_row(total_a, total_b, source_a_headers, source_b_headers))
            source_b_path_str = str(feedback_path)
            source_b_row_count = len(data_b)
        else:
            merged_headers = source_a_headers
            merged_rows = [[row.get(h, "") for h in source_a_headers] for row in top_n_rows]
            if total_a:
                merged_rows.append([total_a.get(h, "") for h in source_a_headers])
            source_b_path_str = None
            source_b_row_count = 0

        report_date = datetime.now().strftime("%d-%m-%Y")
        excel_dir = ensure_directory(resolve_report_dir(config.output_excel_dir, report_slug))
        pdf_dir = ensure_directory(resolve_report_dir(config.output_pdf_dir, report_slug))
        base_name = f"Rail_Madad_Report_2_Division_Wise_Bottom_25_{report_date}"
        excel_path = excel_dir / f"{base_name}.xlsx"
        pdf_path = pdf_dir / f"{base_name}.pdf"

        try:
            self._write_excel(excel_path, merged_headers, merged_rows, report_date=report_date)
            self._write_pdf(pdf_path, merged_headers, merged_rows, report_date=report_date)
        except Exception as exc:
            return ProcessingResult(
                input_row_count=len(data_a),
                success=False,
                error=str(exc),
                source_a_path=str(source_a_path),
                source_b_path=source_b_path_str,
                source_a_rows=len(data_a),
                source_b_rows=source_b_row_count,
            )

        log_automation_event(
            logger,
            "phase8_dataset_loaded",
            source_a=str(source_a_path),
            source_b=source_b_path_str,
            input_row_count=len(data_a),
            top_n_selected=len(top_n_rows),
        )

        return ProcessingResult(
            success=True,
            input_row_count=len(data_a),
            processed_row_count=len(merged_rows),
            excel_path=str(excel_path),
            pdf_path=str(pdf_path),
            source_a_path=str(source_a_path),
            source_b_path=source_b_path_str,
            source_a_rows=len(data_a),
            source_b_rows=source_b_row_count,
        )

    def _find_feedback_csv(self, report_slug: str) -> Path | None:
        extracted_dir = resolve_report_dir(config.extracted_data_dir, report_slug)
        preferred = extracted_dir / FEEDBACK_FILENAME
        if preferred.exists():
            return preferred
        matches = sorted(extracted_dir.glob("*feedback*.csv"))
        return matches[0] if matches else None

    @staticmethod
    def _read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = list(reader.fieldnames or [])
            rows = [{header: row.get(header, "") for header in headers} for row in reader]
        return rows, headers

    @staticmethod
    def _normalize_org(name: str) -> str:
        return re.sub(r"\s+", " ", name.strip()).lower()

    @staticmethod
    def _is_total_row(row: dict[str, str]) -> bool:
        org = row.get("Organisation", "") or row.get("Division", "")
        return "total" in org.strip().lower()

    def _split_total_row(
        self,
        rows: list[dict[str, str]],
    ) -> tuple[list[dict[str, str]], dict[str, str] | None]:
        if not rows:
            return [], None
        if self._is_total_row(rows[-1]):
            return rows[:-1], rows[-1]
        return rows, None

    def _build_feedback_lookup(
        self,
        source_b_rows: list[dict[str, str]],
    ) -> dict[str, dict[str, str]]:
        lookup: dict[str, dict[str, str]] = {}
        for row in source_b_rows:
            org = row.get("Organisation", "") or row.get("Division", "")
            lookup[self._normalize_org(org)] = row
        return lookup

    def _feedback_values_for_row(
        self,
        org: str,
        lookup: dict[str, dict[str, str]],
    ) -> list[str]:
        row = lookup.get(self._normalize_org(org), {})
        return [row.get(column, "") for column in SOURCE_B_DATA_COLUMNS]

    def _merge_rows(
        self,
        source_a_rows: list[dict[str, str]],
        source_a_headers: list[str],
        source_b_rows: list[dict[str, str]],
        source_b_headers: list[str],
    ) -> list[list[str]]:
        lookup = self._build_feedback_lookup(source_b_rows)
        merged: list[list[str]] = []

        for index, row in enumerate(source_a_rows, start=1):
            org = row.get("Organisation", "") or row.get("Division", "")
            source_a_values = [row.get(header, "") for header in source_a_headers]
            b_sno = str(index)
            b_org = org
            b_values = self._feedback_values_for_row(org, lookup)
            merged.append(source_a_values + [b_sno, b_org] + b_values)

        return merged

    def _merge_total_row(
        self,
        total_a: dict[str, str],
        total_b: dict[str, str] | None,
        source_a_headers: list[str],
        source_b_headers: list[str],
    ) -> list[str]:
        a_values = [total_a.get(header, "") for header in source_a_headers]
        b_values = [
            (total_b or {}).get(column, "") for column in SOURCE_B_DATA_COLUMNS
        ]
        b_sno = total_b.get("S.No.", "") if total_b else ""
        b_org = total_b.get("Organisation", "All Divisions") if total_b else "All Divisions"
        return a_values + [b_sno, b_org] + b_values

    def _write_excel(
        self,
        target_path: Path,
        headers: list[str],
        rows: list[list[str]],
        *,
        report_date: str,
    ) -> None:
        temp_path = target_path.with_suffix(target_path.suffix + ".tmp")
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Report 2"

        title = (
            f"Rail Madad Report No 2 - Division Wise Complaints & Feedback Report "
            f"- Bottom 25 Divisions on date {report_date}"
        )
        worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
        title_cell = worksheet.cell(row=1, column=1, value=title)
        title_cell.font = Font(bold=True, size=12)
        title_cell.alignment = Alignment(horizontal="center")

        header_row = 2
        for col_idx, header in enumerate(headers, start=1):
            cell = worksheet.cell(row=header_row, column=col_idx, value=header)
            cell.font = Font(bold=True)
            cell.border = THIN_BORDER

        data_start = 3
        for row_offset, row_values in enumerate(rows):
            row_idx = data_start + row_offset
            for col_idx, value in enumerate(row_values, start=1):
                cell = worksheet.cell(row=row_idx, column=col_idx, value=value)
                cell.border = THIN_BORDER

        for col_idx in HIDDEN_COLUMNS:
            if col_idx <= len(headers):
                worksheet.column_dimensions[get_column_letter(col_idx)].hidden = True

        highlight_south_central_railway_rows(
            worksheet,
            start_row=data_start,
            end_row=worksheet.max_row,
            start_col=1,
            end_col=len(headers),
        )

        if rows:
            totals_row = worksheet.max_row
            for col_idx in range(1, len(headers) + 1):
                cell = worksheet.cell(row=totals_row, column=col_idx)
                cell.font = Font(bold=True)

        workbook.save(temp_path)
        temp_path.replace(target_path)

    def _visible_column_indices(self, headers: list[str]) -> list[int]:
        return [idx for idx in range(1, len(headers) + 1) if idx not in HIDDEN_COLUMNS]

    def _write_pdf(
        self,
        target_path: Path,
        headers: list[str],
        rows: list[list[str]],
        *,
        report_date: str,
    ) -> None:
        temp_path = target_path.with_suffix(target_path.suffix + ".tmp")
        visible_indices = self._visible_column_indices(headers)
        visible_headers = [headers[idx - 1] for idx in visible_indices]

        table_data: list[list[str]] = [visible_headers]
        scr_row_indices: set[int] = set()
        for row_values in rows:
            visible_row = [row_values[idx - 1] if idx <= len(row_values) else "" for idx in visible_indices]
            table_data.append(visible_row)
            if row_contains_scr(visible_row):
                scr_row_indices.add(len(table_data) - 1)

        doc = SimpleDocTemplate(
            str(temp_path),
            pagesize=landscape(A4),
            leftMargin=24,
            rightMargin=24,
            topMargin=24,
            bottomMargin=24,
        )
        styles = getSampleStyleSheet()
        story = [
            Paragraph(
                (
                    f"Rail Madad Report No 2 - Division Wise Complaints &amp; Feedback Report "
                    f"- Bottom 25 Divisions on date {report_date}"
                ),
                styles["Title"],
            ),
            Spacer(1, 12),
        ]

        table = Table(table_data, repeatRows=1)
        style_commands: list[tuple] = [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
        for row_idx in scr_row_indices:
            style_commands.append(("BACKGROUND", (0, row_idx), (-1, row_idx), colors.yellow))
            style_commands.append(("TEXTCOLOR", (0, row_idx), (-1, row_idx), colors.black))
        if rows:
            style_commands.append(("FONTNAME", (0, len(table_data) - 1), (-1, len(table_data) - 1), "Helvetica-Bold"))
        table.setStyle(TableStyle(style_commands))
        story.append(table)
        doc.build(story)
        temp_path.replace(target_path)
