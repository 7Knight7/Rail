"""Shared PDF table layout helpers (fit width, landscape, A3 fallback)."""

from __future__ import annotations

from reportlab.lib.pagesizes import A3, A4, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Table, TableStyle

# Safe margins so first/last columns are not clipped by the page edge.
SAFE_MARGIN_PT = 18.0
MIN_FONT_SIZE = 6.0
MAX_FONT_SIZE = 8.0


def landscape_page_candidates() -> list[tuple[float, float]]:
    """Prefer A4 landscape; fall back to A3 landscape when the table is wide."""
    return [landscape(A4), landscape(A3)]


def _cell_text(value: object) -> str:
    return "" if value is None else str(value)


def preferred_column_widths(
    table_data: list[list[object]],
    *,
    font_name: str = "Helvetica",
    font_size: float = 8.0,
    padding: float = 6.0,
) -> list[float]:
    """Estimate natural column widths from header + body content."""
    if not table_data:
        return []
    col_count = max(len(row) for row in table_data)
    widths = [0.0] * col_count
    for row in table_data:
        for idx in range(col_count):
            text = _cell_text(row[idx] if idx < len(row) else "")
            measured = stringWidth(text, font_name, font_size) + padding
            if measured > widths[idx]:
                widths[idx] = measured
    # Keep a readable minimum so short headers/values still show.
    return [max(w, 22.0) for w in widths]


def fit_column_widths(
    preferred: list[float],
    usable_width: float,
) -> list[float]:
    """Scale column widths to fit usable page width without cropping."""
    if not preferred:
        return []
    total = sum(preferred)
    if total <= 0:
        equal = usable_width / len(preferred)
        return [equal] * len(preferred)
    if total <= usable_width:
        return list(preferred)
    scale = usable_width / total
    return [w * scale for w in preferred]


def choose_landscape_layout(
    table_data: list[list[object]],
    *,
    margin: float = SAFE_MARGIN_PT,
) -> tuple[tuple[float, float], list[float], float, float]:
    """
    Pick landscape page size + colWidths + font size so the table fits one page width.

    Returns (pagesize, col_widths, font_size, margin).
    """
    for pagesize in landscape_page_candidates():
        usable = pagesize[0] - (2 * margin)
        font_size = MAX_FONT_SIZE
        while font_size >= MIN_FONT_SIZE - 1e-9:
            preferred = preferred_column_widths(table_data, font_size=font_size)
            if sum(preferred) <= usable + 0.5:
                return pagesize, preferred, font_size, margin
            font_size -= 0.5

    # Last resort: force-fit onto widest candidate (A3 landscape).
    pagesize = landscape_page_candidates()[-1]
    usable = pagesize[0] - (2 * margin)
    preferred = preferred_column_widths(table_data, font_size=MIN_FONT_SIZE)
    return pagesize, fit_column_widths(preferred, usable), MIN_FONT_SIZE, margin


def build_fitted_table(
    table_data: list[list[object]],
    style_commands: list[tuple],
    *,
    margin: float = SAFE_MARGIN_PT,
) -> tuple[Table, tuple[float, float], float]:
    """
    Build a Table that fits landscape A4 or A3 without horizontal clipping.

    Returns (table, pagesize, margin).
    """
    pagesize, col_widths, font_size, used_margin = choose_landscape_layout(
        table_data,
        margin=margin,
    )
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    commands = list(style_commands)
    commands.extend(
        [
            ("FONTSIZE", (0, 0), (-1, -1), font_size),
            ("FONTSIZE", (0, 0), (-1, 0), max(font_size, MIN_FONT_SIZE)),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
    )
    table.setStyle(TableStyle(commands))
    usable = pagesize[0] - (2 * used_margin)
    wrapped_w, _ = table.wrap(usable, pagesize[1])
    if wrapped_w > usable + 1.0:
        # Final guard: rescale once more if wrap still overflows.
        scale = usable / wrapped_w
        table = Table(
            table_data,
            colWidths=[w * scale for w in col_widths],
            repeatRows=1,
        )
        table.setStyle(TableStyle(commands))
    return table, pagesize, used_margin
