"""Generate dataset column metadata from an original imported dataset."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any

from app.core.spreadsheet.excel_reader import ExcelDataset, ExcelDatasetMetadata
from app.core.spreadsheet.parser import ColumnDataType

DEFAULT_UNIQUE_VALUE_LIMIT = 50


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _serialize_unique_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _is_sortable(data_type: ColumnDataType) -> bool:
    return data_type in {"text", "number", "date", "status", "boolean"}


def _is_filterable(data_type: ColumnDataType) -> bool:
    return data_type in {"text", "number", "date", "status", "boolean"}


@dataclass(frozen=True)
class ColumnMetadataEntry:
    id: str
    index: int
    name: str
    data_type: ColumnDataType
    nullable: bool
    unique_values: list[Any]
    unique_value_count: int
    filterable: bool
    sortable: bool

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["display_name"] = self.name
        payload["field_name"] = self.name
        return payload


@dataclass(frozen=True)
class GeneratedDatasetMetadata:
    columns: list[ColumnMetadataEntry]
    row_count: int
    column_count: int
    source: ExcelDatasetMetadata

    def to_dict(self) -> dict[str, Any]:
        return {
            "columns": [column.to_dict() for column in self.columns],
            "row_count": self.row_count,
            "column_count": self.column_count,
            "source": self.source.to_dict(),
        }


@dataclass(frozen=True)
class DatasetWithMetadata:
    """Original rows kept separate from generated metadata."""

    rows: list[list[Any]]
    metadata: GeneratedDatasetMetadata

    def to_dict(self) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "metadata": self.metadata.to_dict(),
        }


class DatasetMetadataService:
    """Build column metadata from an original dataset without mutating row data."""

    def __init__(self, *, unique_value_limit: int = DEFAULT_UNIQUE_VALUE_LIMIT) -> None:
        self._unique_value_limit = unique_value_limit

    def generate(self, dataset: ExcelDataset) -> GeneratedDatasetMetadata:
        columns = [
            self._build_column_metadata(column.index, column.name, column.data_type, dataset.rows)
            for column in dataset.columns
        ]
        return GeneratedDatasetMetadata(
            columns=columns,
            row_count=len(dataset.rows),
            column_count=len(columns),
            source=dataset.metadata,
        )

    def split(self, dataset: ExcelDataset) -> DatasetWithMetadata:
        return DatasetWithMetadata(
            rows=dataset.rows,
            metadata=self.generate(dataset),
        )

    def _build_column_metadata(
        self,
        index: int,
        name: str,
        data_type: ColumnDataType,
        rows: list[list[Any]],
    ) -> ColumnMetadataEntry:
        values = [row[index] if index < len(row) else None for row in rows]
        nullable = any(_is_empty(value) for value in values)
        unique_values, unique_value_count = self._collect_unique_values(values)

        return ColumnMetadataEntry(
            id=str(uuid.uuid4()),
            index=index,
            name=name,
            data_type=data_type,
            nullable=nullable,
            unique_values=unique_values,
            unique_value_count=unique_value_count,
            filterable=_is_filterable(data_type),
            sortable=_is_sortable(data_type),
        )

    def _collect_unique_values(self, values: list[Any]) -> tuple[list[Any], int]:
        seen: list[Any] = []
        observed: set[str] = set()

        for value in values:
            if _is_empty(value):
                continue

            serialized = _serialize_unique_value(value)
            key = repr(serialized)
            if key in observed:
                continue

            observed.add(key)
            seen.append(serialized)

        unique_value_count = len(seen)
        if unique_value_count > self._unique_value_limit:
            return seen[: self._unique_value_limit], unique_value_count
        return seen, unique_value_count


def generate_dataset_metadata(dataset: ExcelDataset) -> GeneratedDatasetMetadata:
    return DatasetMetadataService().generate(dataset)
