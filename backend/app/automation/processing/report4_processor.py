"""Report 4 post-ingestion processor (Cause-wise Top 10 Trains - 7 Types)."""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.automation.config import config
from app.automation.formatting.scr import highlight_south_central_railway_rows, row_contains_scr
from app.automation.processing.base import ProcessingResult
from app.automation.report4_filters import COMPLAINT_TYPES_ORDERED, get_type_configs, TypeConfig
from app.automation.utils import (
    ensure_directory,
    log_automation_event,
    previous_day_report_date,
    resolve_report_dir,
)

logger = logging.getLogger(__name__)

PROCESSOR_NAME = "report4_causewise_top10_processor"

TOP_N = 10

OUTPUT_HEADERS = [
    "S.No.",
    "Train Name",
    "Owning Zone",
    "Owning Division",
    "Train No.",
    "Received",
]

THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)


@dataclass
class TypeDataset:
    """Data for a single complaint type section."""
    
    type_config: TypeConfig
    rows: list[list[str]]


class Report4Processor:
    """Process Cause-wise Top 10 Trains datasets and emit formatted Excel/PDF."""

    processor_name = PROCESSOR_NAME

    def process(
        self,
        *,
        source_a_path: Path,
        report_slug: str,
        source_b_path: Path | None = None,
        type_datasets: dict[str, list[dict[str, str]]] | None = None,
    ) -> ProcessingResult:
        """Process Report 4 with 7 complaint type sections.
        
        If type_datasets is provided, use it directly.
        Otherwise, load from individual CSV files per type.
        """
        if source_a_path.suffix.lower() == ".pdf":
            return ProcessingResult(success=False, error="PDF cannot be used as processing input")

        type_configs = get_type_configs()
        sections: list[TypeDataset] = []
        total_input_rows = 0

        if type_datasets:
            for type_config in type_configs:
                raw_rows = type_datasets.get(type_config.name, [])
                data_rows = self._exclude_total_rows(raw_rows)
                top_rows = data_rows[:TOP_N]
                formatted = self._format_output_rows(top_rows)
                sections.append(TypeDataset(type_config=type_config, rows=formatted))
                total_input_rows += len(data_rows)
        else:
            base_dir = resolve_report_dir(config.extracted_data_dir, report_slug)
            for type_config in type_configs:
                type_slug = type_config.name.lower().replace(" ", "_").replace("&", "and")
                csv_path = base_dir / f"report4_{type_slug}_raw.csv"
                
                if csv_path.exists():
                    raw_rows, _ = self._read_csv(csv_path)
                    data_rows = self._exclude_total_rows(raw_rows)
                    top_rows = data_rows[:TOP_N]
                    formatted = self._format_output_rows(top_rows)
                    total_input_rows += len(data_rows)
                else:
                    formatted = []
                    log_automation_event(
                        logger,
                        "type_csv_not_found",
                        type_name=type_config.name,
                        expected_path=str(csv_path),
                    )
                
                sections.append(TypeDataset(type_config=type_config, rows=formatted))

        report_date = previous_day_report_date()
        excel_dir = ensure_directory(resolve_report_dir(config.output_excel_dir, report_slug))
        pdf_dir = ensure_directory(resolve_report_dir(config.output_pdf_dir, report_slug))
        base_name = f"Rail_Madad_Report_4_Cause_Wise_Top_10_Trains_{report_date}"
        excel_path = excel_dir / f"{base_name}.xlsx"
        pdf_path = pdf_dir / f"{base_name}.pdf"

        try:
            self._write_excel(excel_path, sections, report_date=report_date)
            self._write_pdf(pdf_path, sections, report_date=report_date)
        except Exception as exc:
            return ProcessingResult(
                input_row_count=total_input_rows,
                success=False,
                error=str(exc),
                source_a_path=str(source_a_path),
                source_a_rows=total_input_rows,
            )

        total_output_rows = sum(len(s.rows) for s in sections)
        
        log_automation_event(
            logger,
            "phase8_dataset_loaded",
            source_a=str(source_a_path),
            input_row_count=total_input_rows,
            section_count=len(sections),
            total_output_rows=total_output_rows,
        )

        return ProcessingResult(
            success=True,
            input_row_count=total_input_rows,
            processed_row_count=total_output_rows,
            excel_path=str(excel_path),
            pdf_path=str(pdf_path),
            source_a_path=str(source_a_path),
            source_a_rows=total_input_rows,
        )

    @staticmethod
    def _read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = list(reader.fieldnames or [])
            rows = [{header: row.get(header, "") for header in headers} for row in reader]
        return rows, headers

    @staticmethod
    def _is_total_row(row: dict[str, str]) -> bool:
        for key in ("Train No.", "Train Name", "Owning Zone"):
            val = row.get(key, "")
            if "total" in val.strip().lower():
                return True
        return False

    def _exclude_total_rows(
        self,
        rows: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        return [r for r in rows if not self._is_total_row(r)]

    def _format_output_rows(
        self,
        rows: list[dict[str, str]],
    ) -> list[list[str]]:
        output: list[list[str]] = []
        for idx, row in enumerate(rows, start=1):
            train_no = row.get("Train No.", "") or row.get("Train No", "")
            train_name = row.get("Train Name", "")
            owning_zone = row.get("Owning Zone", "")
            owning_division = row.get("Owning Division", "")
            received = row.get("Received", "")

            output.append([
                str(idx),
                train_name,
                owning_zone,
                owning_division,
                train_no,
                received,
            ])
        return output

    def _write_excel(
        self,
        target_path: Path,
        sections: list[TypeDataset],
        *,
        report_date: str,
    ) -> None:
        temp_path = target_path.with_suffix(target_path.suffix + ".tmp")
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Report 4"

        main_title = (
            f"Rail Madad Report No 4 - Cause wise Top 10 Trains "
            f"on date {report_date}"
        )
        worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(OUTPUT_HEADERS))
        title_cell = worksheet.cell(row=1, column=1, value=main_title)
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal="center")

        current_row = 3

        for section in sections:
            worksheet.merge_cells(
                start_row=current_row,
                start_column=1,
                end_row=current_row,
                end_column=len(OUTPUT_HEADERS),
            )
            section_title_cell = worksheet.cell(
                row=current_row,
                column=1,
                value=section.type_config.section_title,
            )
            section_title_cell.font = Font(bold=True, size=11)
            section_title_cell.alignment = Alignment(horizontal="left")
            current_row += 1

            for col_idx, header in enumerate(OUTPUT_HEADERS, start=1):
                cell = worksheet.cell(row=current_row, column=col_idx, value=header)
                cell.font = Font(bold=True)
                cell.border = THIN_BORDER
            header_row = current_row
            current_row += 1

            data_start = current_row
            for row_values in section.rows:
                for col_idx, value in enumerate(row_values, start=1):
                    cell = worksheet.cell(row=current_row, column=col_idx, value=value)
                    cell.border = THIN_BORDER
                    if col_idx == 5:
                        cell.number_format = "@"
                current_row += 1

            if section.rows:
                highlight_south_central_railway_rows(
                    worksheet,
                    start_row=data_start,
                    end_row=current_row - 1,
                    start_col=1,
                    end_col=len(OUTPUT_HEADERS),
                )

            current_row += 1

        workbook.save(temp_path)
        temp_path.replace(target_path)

    def _write_pdf(
        self,
        target_path: Path,
        sections: list[TypeDataset],
        *,
        report_date: str,
    ) -> None:
        temp_path = target_path.with_suffix(target_path.suffix + ".tmp")

        doc = SimpleDocTemplate(
            str(temp_path),
            pagesize=landscape(A4),
            leftMargin=24,
            rightMargin=24,
            topMargin=24,
            bottomMargin=24,
        )
        styles = getSampleStyleSheet()
        section_style = ParagraphStyle(
            "SectionTitle",
            parent=styles["Heading2"],
            fontSize=11,
            spaceAfter=6,
        )

        story = [
            Paragraph(
                f"Rail Madad Report No 4 - Cause wise Top 10 Trains on date {report_date}",
                styles["Title"],
            ),
            Spacer(1, 12),
        ]

        for section in sections:
            story.append(Paragraph(section.type_config.section_title, section_style))
            story.append(Spacer(1, 6))

            table_data: list[list[str]] = [OUTPUT_HEADERS]
            scr_row_indices: set[int] = set()
            for row_values in section.rows:
                table_data.append(row_values)
                if row_contains_scr(row_values):
                    scr_row_indices.add(len(table_data) - 1)

            if len(table_data) > 1:
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
            else:
                story.append(Paragraph("No data available for this type.", styles["Normal"]))

            story.append(Spacer(1, 12))

        doc.build(story)
        temp_path.replace(target_path)
