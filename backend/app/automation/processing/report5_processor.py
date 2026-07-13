"""Report 5 post-ingestion processor (SCR Train Mode Unsatisfactory Feedback)."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, Side
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.automation.config import config
from app.automation.formatting.scr import (
    highlight_south_central_railway_rows,
    mode_matches,
    row_contains_scr,
)
from app.automation.processing.base import ProcessingResult
from app.automation.utils import (
    ensure_directory,
    log_automation_event,
    previous_day_report_date,
    resolve_report_dir,
)

logger = logging.getLogger(__name__)

PROCESSOR_NAME = "report5_scr_train_processor"

TEMPLATE_FILENAME = "scr_train_original.xlsx"
TEMPLATE_MISSING_ERROR = "REPORT5_TEMPLATE_OR_FORMULA_MISSING"

OUTPUT_HEADERS = [
    "S.No.",
    "Ref. No.",
    "Complaint Date",
    "Train/Station",
    "Mode",
    "Type",
    "Sub Type",
    "Department",
    "Status",
]

THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)


class Report5Processor:
    """Process SCR Train Mode Unsatisfactory Feedback dataset."""

    processor_name = PROCESSOR_NAME
    expected_mode = "Train"

    def process(
        self,
        *,
        source_a_path: Path,
        report_slug: str,
        source_b_path: Path | None = None,
    ) -> ProcessingResult:
        if source_a_path.suffix.lower() == ".pdf":
            return ProcessingResult(success=False, error="PDF cannot be used as processing input")

        source_rows, source_headers = self._read_csv(source_a_path)
        
        train_rows = [
            row for row in source_rows
            if mode_matches(self.expected_mode, row.get("Mode", ""))
        ]

        if not train_rows:
            return ProcessingResult(
                success=False,
                error=f"No {self.expected_mode} mode rows found in data",
                input_row_count=len(source_rows),
                source_a_path=str(source_a_path),
            )

        output_rows = self._format_output_rows(train_rows)

        report_date = previous_day_report_date()
        excel_dir = ensure_directory(resolve_report_dir(config.output_excel_dir, report_slug))
        pdf_dir = ensure_directory(resolve_report_dir(config.output_pdf_dir, report_slug))
        base_name = f"Rail_Madad_Report_5_SCR_Train_Unsatisfactory_{report_date}"
        excel_path = excel_dir / f"{base_name}.xlsx"
        pdf_path = pdf_dir / f"{base_name}.pdf"

        template_path = self._find_template()
        
        try:
            if template_path and template_path.exists():
                self._write_excel_from_template(
                    template_path,
                    excel_path,
                    OUTPUT_HEADERS,
                    output_rows,
                    report_date=report_date,
                )
            else:
                log_automation_event(
                    logger,
                    "template_not_found",
                    expected_path=str(template_path) if template_path else "N/A",
                    fallback="programmatic_generation",
                )
                self._write_excel(excel_path, OUTPUT_HEADERS, output_rows, report_date=report_date)

            self._write_pdf(pdf_path, OUTPUT_HEADERS, output_rows, report_date=report_date)
        except Exception as exc:
            return ProcessingResult(
                input_row_count=len(source_rows),
                success=False,
                error=str(exc),
                source_a_path=str(source_a_path),
                source_a_rows=len(source_rows),
            )

        log_automation_event(
            logger,
            "phase8_dataset_loaded",
            source_a=str(source_a_path),
            input_row_count=len(source_rows),
            output_row_count=len(output_rows),
            mode=self.expected_mode,
        )

        return ProcessingResult(
            success=True,
            input_row_count=len(source_rows),
            processed_row_count=len(output_rows),
            excel_path=str(excel_path),
            pdf_path=str(pdf_path),
            source_a_path=str(source_a_path),
            source_a_rows=len(source_rows),
        )

    def _find_template(self) -> Path | None:
        """Find the template workbook."""
        possible_paths = [
            Path(config.output_excel_dir).parent / "templates" / TEMPLATE_FILENAME,
            Path(__file__).parent.parent.parent / "infrastructure" / "seed" / "sample_workbooks" / TEMPLATE_FILENAME,
            Path(config.output_excel_dir) / TEMPLATE_FILENAME,
        ]
        for path in possible_paths:
            if path.exists():
                return path
        return None

    @staticmethod
    def _read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = list(reader.fieldnames or [])
            rows = [{header: row.get(header, "") for header in headers} for row in reader]
        return rows, headers

    def _format_output_rows(
        self,
        rows: list[dict[str, str]],
    ) -> list[list[str]]:
        output: list[list[str]] = []
        for idx, row in enumerate(rows, start=1):
            output.append([
                str(idx),
                row.get("Ref. No.", ""),
                (
                    row.get("Complaint Date", "")
                    or row.get("Date", "")
                    or row.get("Registration Date", "")
                ),
                row.get("Train/Station", "") or row.get("Train", ""),
                self.expected_mode,
                row.get("Type", ""),
                row.get("Sub Type", "") or row.get("SubType", ""),
                row.get("Department", "") or row.get("Dept", ""),
                row.get("Status", ""),
            ])
        return output

    def _write_excel_from_template(
        self,
        template_path: Path,
        target_path: Path,
        headers: list[str],
        rows: list[list[str]],
        *,
        report_date: str,
    ) -> None:
        """Write Excel using template, preserving formulas and formatting."""
        temp_path = target_path.with_suffix(target_path.suffix + ".tmp")
        workbook = load_workbook(str(template_path))
        worksheet = workbook.active

        data_start_row = 4
        for row_offset, row_values in enumerate(rows):
            row_idx = data_start_row + row_offset
            for col_idx, value in enumerate(row_values, start=1):
                cell = worksheet.cell(row=row_idx, column=col_idx, value=value)
                cell.border = THIN_BORDER

        highlight_south_central_railway_rows(
            worksheet,
            start_row=data_start_row,
            end_row=worksheet.max_row,
            start_col=1,
            end_col=len(headers),
        )

        workbook.save(temp_path)
        temp_path.replace(target_path)

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
        worksheet.title = "Report 5"

        title = (
            f"Rail Madad Report No 5 - SCR {self.expected_mode} Mode Unsatisfactory Feedback "
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

        highlight_south_central_railway_rows(
            worksheet,
            start_row=data_start,
            end_row=worksheet.max_row,
            start_col=1,
            end_col=len(headers),
        )

        workbook.save(temp_path)
        temp_path.replace(target_path)

    def _write_pdf(
        self,
        target_path: Path,
        headers: list[str],
        rows: list[list[str]],
        *,
        report_date: str,
    ) -> None:
        temp_path = target_path.with_suffix(target_path.suffix + ".tmp")

        table_data: list[list[str]] = [headers]
        scr_row_indices: set[int] = set()
        for row_values in rows:
            table_data.append(row_values)
            if row_contains_scr(row_values):
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
                f"Rail Madad Report No 5 - SCR {self.expected_mode} Mode Unsatisfactory Feedback on date {report_date}",
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
        table.setStyle(TableStyle(style_commands))
        story.append(table)
        doc.build(story)
        temp_path.replace(target_path)
