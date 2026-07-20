"""Top-N (Report 3 / Report 4) PDF landscape fit layout.

A3 landscape by default, A2 when needed. Explicit column roles so first/last
columns stay fully visible within the printable width.
"""

from __future__ import annotations

from reportlab.lib.pagesizes import A2, A3, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle

from app.automation.formatting.pdf_fonts import (
    ensure_pdf_unicode_fonts,
    pdf_font_bold,
    pdf_font_regular,
)
from app.automation.formatting.pdf_table import (
    _build_table,
    _cell_text,
    _escape_paragraph_text,
    _rescale_if_overflow,
    prepare_wrapped_table_data,
)

# Safe narrow margins — first/last column borders stay on-page.
TOPN_SAFE_MARGIN_PT = 18.0
TOPN_BODY_FONT_PT = 8.5
TOPN_HEADER_FONT_PT = 9.0
TOPN_TITLE_FONT_PT = 16.0
TOPN_SECTION_FONT_PT = 12.0

# Relative weights for selected Top-N columns (Train Name widest).
_TOPN_COLUMN_WEIGHTS: dict[str, float] = {
    "s.no.": 0.55,
    "s.no": 0.55,
    "train name": 3.4,
    "owning zone": 1.85,
    "owning division": 1.85,
    "train no.": 0.75,
    "train no": 0.75,
    "received": 0.7,
    "% share": 0.7,
    "closed": 0.7,
    "% closed": 0.7,
    "pending": 0.7,
    "average rating": 1.35,
}
_DEFAULT_WEIGHT = 1.0
_MIN_COL_PT = 28.0


def topn_landscape_candidates() -> list[tuple[float, float]]:
    """A3 landscape default; A2 when the table still cannot fit."""
    return [landscape(A3), landscape(A2)]


def _column_weight(header: str) -> float:
    key = _cell_text(header).strip().lower()
    return _TOPN_COLUMN_WEIGHTS.get(key, _DEFAULT_WEIGHT)


def allocate_topn_column_widths(headers: list[str], usable_width: float) -> list[float]:
    """Allocate printable width: Train Name widest, metrics compact, rating medium."""
    if not headers:
        return []
    weights = [_column_weight(h) for h in headers]
    total = sum(weights) or float(len(headers))
    widths = [usable_width * w / total for w in weights]
    floors = [max(w, _MIN_COL_PT) for w in widths]
    floor_total = sum(floors)
    if floor_total <= usable_width:
        leftover = usable_width - floor_total
        prefer_idx = 0
        for idx, header in enumerate(headers):
            if _column_weight(header) >= 3.0:
                prefer_idx = idx
                break
        floors[prefer_idx] += leftover
        return floors
    scale = usable_width / floor_total
    return [w * scale for w in floors]


def choose_topn_landscape_layout(
    headers: list[str],
    *,
    margin: float = TOPN_SAFE_MARGIN_PT,
) -> tuple[tuple[float, float], list[float], float]:
    """
    Pick landscape page + colWidths so the table fits one page wide.

    fitToWidth=1 analogue: never split horizontally; paginate vertically only.
    """
    for pagesize in topn_landscape_candidates():
        usable = pagesize[0] - (2 * margin)
        col_widths = allocate_topn_column_widths(headers, usable)
        if sum(col_widths) <= usable + 0.5:
            return pagesize, col_widths, margin
    pagesize = topn_landscape_candidates()[-1]
    usable = pagesize[0] - (2 * margin)
    return pagesize, allocate_topn_column_widths(headers, usable), margin


def topn_title_style(name: str = "TopnTitle") -> ParagraphStyle:
    ensure_pdf_unicode_fonts()
    return ParagraphStyle(
        name,
        fontName=pdf_font_bold(),
        fontSize=TOPN_TITLE_FONT_PT,
        leading=TOPN_TITLE_FONT_PT + 3,
        alignment=1,  # TA_CENTER
        spaceAfter=8,
    )


def topn_section_style(name: str = "TopnSection") -> ParagraphStyle:
    ensure_pdf_unicode_fonts()
    return ParagraphStyle(
        name,
        fontName=pdf_font_bold(),
        fontSize=TOPN_SECTION_FONT_PT,
        leading=TOPN_SECTION_FONT_PT + 3,
        spaceBefore=4,
        spaceAfter=10,
    )


def build_topn_title_block(title_text: str, table_width: float) -> Table:
    """Center the title across the exact table width (not the full page frame)."""
    para = Paragraph(_escape_paragraph_text(title_text), topn_title_style())
    title_table = Table([[para]], colWidths=[table_width])
    title_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return title_table


def build_topn_fitted_table(
    table_data: list[list[object]],
    style_commands: list[tuple],
    *,
    margin: float = TOPN_SAFE_MARGIN_PT,
    body_font_size: float = TOPN_BODY_FONT_PT,
    header_font_size: float = TOPN_HEADER_FONT_PT,
) -> tuple[Table, tuple[float, float], float, list[float]]:
    """
    Build a Top-N table that fits A3/A2 landscape without horizontal cropping.

    Returns (table, pagesize, margin, col_widths).
    """
    if not table_data:
        raise ValueError("table_data must not be empty")
    headers = [_cell_text(h) for h in table_data[0]]
    pagesize, col_widths, used_margin = choose_topn_landscape_layout(headers, margin=margin)

    wrap_headers = {
        h
        for h in headers
        if _column_weight(h) >= 1.3  # Train Name, Zone, Division, Average Rating
    }
    wrapped = prepare_wrapped_table_data(
        table_data,
        headers,
        wrap_headers,
        body_font_size,
        wrap_all=True,
    )
    ensure_pdf_unicode_fonts()
    header_style = ParagraphStyle(
        name="TopnPdfHeader",
        fontName=pdf_font_bold(),
        fontSize=header_font_size,
        leading=header_font_size + 1.5,
        wordWrap="CJK",
    )
    wrapped[0] = [
        Paragraph(_escape_paragraph_text(_cell_text(cell)), header_style)
        for cell in table_data[0]
    ]

    table = _build_table(wrapped, col_widths, splittable=True, repeat_rows=1)
    commands = list(style_commands)
    commands.extend(
        [
            ("FONTSIZE", (0, 1), (-1, -1), body_font_size),
            ("FONTSIZE", (0, 0), (-1, 0), header_font_size),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTNAME", (0, 1), (-1, -1), pdf_font_regular()),
            ("FONTNAME", (0, 0), (-1, 0), pdf_font_bold()),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ]
    )
    table.setStyle(TableStyle(commands))
    table = _rescale_if_overflow(
        wrapped,
        table,
        col_widths,
        commands,
        pagesize,
        used_margin,
        splittable=True,
    )
    return table, pagesize, used_margin, list(col_widths)
