"""Shared report formatting utilities."""

from app.automation.formatting.pdf_table import build_fitted_table
from app.automation.formatting.scr import highlight_south_central_railway_rows
from app.automation.formatting.serial import apply_serial_number, is_serial_header, renumber_data_rows

__all__ = [
    "apply_serial_number",
    "build_fitted_table",
    "highlight_south_central_railway_rows",
    "is_serial_header",
    "renumber_data_rows",
]
