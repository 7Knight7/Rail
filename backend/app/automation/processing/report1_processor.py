"""Report 1 post-ingestion processor (Comprehensive + Feedback merge)."""

from __future__ import annotations

import csv
import logging
import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.automation.config import config
from app.automation.formatting.pdf_table import build_fitted_table
from app.automation.formatting.scr import row_contains_scr
from app.automation.formatting.serial import apply_serial_number
from app.automation.processing.base import ProcessingResult
from app.automation.utils import (
    ensure_directory,
    log_automation_event,
    previous_day_report_date,
    resolve_report_dir,
)

logger = logging.getLogger(__name__)

PROCESSOR_NAME = "report1_zone_wise_processor"

FEEDBACK_FILENAME = "report1_feedback_zone_raw.csv"
SOURCE_B_DATA_COLUMNS = [
    "Feedback Received",
    "% Feedback",
    "Excellent",
    "Satisfactory",
    "Unsatisfactory",
    "% Unsatisfactory",
]
HIDDEN_COLUMNS = {3, 7, 10, 11, 12, 13, 14, 15}
THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)


class Report1Processor:
    """Merge Comprehensive + Feedback datasets and emit formatted Excel/PDF."""

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
        if feedback_path is None:
            expected = resolve_report_dir(config.extracted_data_dir, report_slug) / FEEDBACK_FILENAME
            return ProcessingResult(
                success=False,
                source_a_path=str(source_a_path),
                error=f"Feedback dataset missing: expected {expected}",
            )

        source_a_rows, source_a_headers = self._read_csv(source_a_path)
        source_b_rows, source_b_headers = self._read_csv(feedback_path)

        data_a, total_a = self._split_total_row(source_a_rows)
        data_b, total_b = self._split_total_row(source_b_rows)

        merged_headers = source_a_headers + ["S.No.", "Organisation"] + SOURCE_B_DATA_COLUMNS
        merged_rows = self._merge_rows(data_a, source_a_headers, data_b, source_b_headers)
        if total_a:
            merged_rows.append(self._merge_total_row(total_a, total_b, source_a_headers, source_b_headers))

        report_date = previous_day_report_date()
        excel_dir = ensure_directory(
            resolve_report_dir(config.output_excel_dir, report_slug)
        )
        pdf_dir = ensure_directory(
            resolve_report_dir(config.output_pdf_dir, report_slug)
        )
        base_name = f"Rail_Madad_Report_1_Zone_Wise_Complaints_Feedback_{report_date}"
        excel_path = excel_dir / f"{base_name}.xlsx"
        pdf_path = pdf_dir / f"{base_name}.pdf"

        try:
            self._write_excel(
                excel_path,
                merged_headers,
                merged_rows,
                report_date=report_date,
            )
            self._write_pdf(
                pdf_path,
                merged_headers,
                merged_rows,
                report_date=report_date,
            )
        except Exception as exc:
            return ProcessingResult(
                input_row_count=len(data_a) + len(data_b),
                success=False,
                error=str(exc),
                source_a_path=str(source_a_path),
                source_b_path=str(feedback_path),
                source_a_rows=len(data_a),
                source_b_rows=len(data_b),
            )

        log_automation_event(
            logger,
            "phase8_dataset_loaded",
            source_a=str(source_a_path),
            source_b=str(feedback_path),
            input_row_count=len(data_a) + len(data_b),
        )

        return ProcessingResult(
            success=True,
            input_row_count=len(data_a) + len(data_b),
            processed_row_count=len(merged_rows),
            excel_path=str(excel_path),
            pdf_path=str(pdf_path),
            source_a_path=str(source_a_path),
            source_b_path=str(feedback_path),
            source_a_rows=len(data_a),
            source_b_rows=len(data_b),
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
        org = row.get("Organisation", "")
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

    @staticmethod
    def _is_irctc_catering(org: str) -> bool:
        normalized = Report1Processor._normalize_org(org)
        return "irctc-catering" in normalized or normalized == "irctc catering"

    @staticmethod
    def _is_irctc_online(org: str) -> bool:
        normalized = Report1Processor._normalize_org(org)
        return "irctc-online" in normalized or normalized == "irctc online"

    @staticmethod
    def _is_irctc_combined(org: str) -> bool:
        return Report1Processor._normalize_org(org) == "irctc"

    def _build_feedback_lookup(
        self,
        source_b_rows: list[dict[str, str]],
    ) -> dict[str, dict[str, str]]:
        lookup: dict[str, dict[str, str]] = {}
        irctc_row: dict[str, str] | None = None
        for row in source_b_rows:
            org = row.get("Organisation", "")
            if self._is_irctc_combined(org):
                irctc_row = row
                continue
            lookup[self._normalize_org(org)] = row
        if irctc_row is not None:
            lookup["__irctc__"] = irctc_row
        return lookup

    def _feedback_values_for_row(
        self,
        org: str,
        lookup: dict[str, dict[str, str]],
        *,
        is_second_irctc: bool,
    ) -> list[str]:
        if is_second_irctc:
            return [""] * len(SOURCE_B_DATA_COLUMNS)

        if self._is_irctc_catering(org) and "__irctc__" in lookup:
            row = lookup["__irctc__"]
        else:
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
            org = row.get("Organisation", "")
            is_second_irctc = self._is_irctc_online(org)

            source_a_values = apply_serial_number(
                source_a_headers,
                [row.get(header, "") for header in source_a_headers],
                index,
            )
            b_sno = str(index)
            b_org = org
            b_values = self._feedback_values_for_row(
                org,
                lookup,
                is_second_irctc=is_second_irctc,
            )
            merged.append(source_a_values + [b_sno, b_org] + b_values)

        return merged

    def _merge_total_row(
        self,
        total_a: dict[str, str],
        total_b: dict[str, str] | None,
        source_a_headers: list[str],
        source_b_headers: list[str],
    ) -> list[str]:
        a_values = apply_serial_number(
            source_a_headers,
            [total_a.get(header, "") for header in source_a_headers],
            None,
        )
        b_values = [
            (total_b or {}).get(column, "") for column in SOURCE_B_DATA_COLUMNS
        ]
        b_sno = ""
        b_org = total_b.get("Organisation", "Total") if total_b else "Total"
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
        worksheet.title = "Report 1"

        title = (
            f"Rail Madad Report No 1 - Zone Wise Complaints & Feedback Report "
            f"on date {report_date}"
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
            worksheet.column_dimensions[get_column_letter(col_idx)].hidden = True

        from app.automation.formatting.scr import highlight_south_central_railway_rows

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
            visible_row = [row_values[idx - 1] for idx in visible_indices]
            table_data.append(visible_row)
            if row_contains_scr(visible_row):
                scr_row_indices.add(len(table_data) - 1)

        style_commands: list[tuple] = [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
        for row_idx in scr_row_indices:
            style_commands.append(("BACKGROUND", (0, row_idx), (-1, row_idx), colors.yellow))
            style_commands.append(("TEXTCOLOR", (0, row_idx), (-1, row_idx), colors.black))
        if rows:
            style_commands.append(
                ("FONTNAME", (0, len(table_data) - 1), (-1, len(table_data) - 1), "Helvetica-Bold")
            )

        table, pagesize, margin = build_fitted_table(table_data, style_commands)
        doc = SimpleDocTemplate(
            str(temp_path),
            pagesize=pagesize,
            leftMargin=margin,
            rightMargin=margin,
            topMargin=margin,
            bottomMargin=margin,
        )
        styles = getSampleStyleSheet()
        story = [
            Paragraph(
                (
                    f"Rail Madad Report No 1 - Zone Wise Complaints &amp; Feedback Report "
                    f"on date {report_date}"
                ),
                styles["Title"],
            ),
            Spacer(1, 12),
            table,
        ]
        doc.build(story)
        temp_path.replace(target_path)
