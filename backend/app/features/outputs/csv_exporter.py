"""Write processed datasets to CSV files."""

from __future__ import annotations

import csv
from pathlib import Path

from app.features.processing.schemas import ProcessDatasetResponse


class CsvExporter:
    def write(self, processed: ProcessDatasetResponse, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        column_names = [column.name for column in processed.columns]

        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=column_names)
            writer.writeheader()
            for row in processed.rows:
                writer.writerow({column: row.get(column, "") for column in column_names})

        return output_path
