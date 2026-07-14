"""Processing result types for Phase 8."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProcessingResult:
    """Outcome of post-ingestion report processing."""

    attempted: bool = False
    success: bool = False
    processor_used: str | None = None
    input_row_count: int = 0
    processed_row_count: int = 0
    excel_path: str | None = None
    pdf_path: str | None = None
    error: str | None = None
    source_a_path: str | None = None
    source_b_path: str | None = None
    source_a_rows: int = 0
    source_b_rows: int = 0
    source_a_mtime: float | None = None
    source_b_mtime: float | None = None
    output_mtime: float | None = None
    run_timestamp: str | None = None
