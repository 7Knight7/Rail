"""Write processed datasets to PDF reports."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.features.processing.schemas import ProcessDatasetResponse

MAX_PDF_ROWS = 100


class PdfExporter:
    """Export processed dataset rows to a PDF report."""

    def write(self, processed: ProcessDatasetResponse, report_name: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=landscape(A4),
            leftMargin=24,
            rightMargin=24,
            topMargin=24,
            bottomMargin=24,
        )

        styles = getSampleStyleSheet()
        story = [
            Paragraph(report_name, styles["Title"]),
            Spacer(1, 12),
            Paragraph(
                f"Rows: {processed.row_count} · Columns: {processed.column_count}",
                styles["Normal"],
            ),
            Spacer(1, 16),
        ]

        column_names = [column.name for column in processed.columns]
        table_data = [column_names]
        for row in processed.rows[:MAX_PDF_ROWS]:
            table_data.append([str(row.get(column, "")) for column in column_names])

        if processed.row_count > MAX_PDF_ROWS:
            story.append(
                Paragraph(
                    f"Showing first {MAX_PDF_ROWS} of {processed.row_count} rows.",
                    styles["Italic"],
                )
            )
            story.append(Spacer(1, 8))

        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(table)
        doc.build(story)
        return output_path
