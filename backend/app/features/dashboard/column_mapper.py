"""Resolve column names from processed report rows."""

from __future__ import annotations

from typing import Any

COLUMN_ALIASES: dict[str, list[str]] = {
    "grievance_id": ["grievance id", "grievance_id", "id"],
    "zone": ["zone"],
    "division": ["division"],
    "train": ["train no", "train number", "train_no", "train"],
    "station": ["station"],
    "category": ["category", "complaint type", "complaint_type", "type"],
    "status": ["current status", "status"],
    "feedback": ["feedback"],
    "registration_date": ["registration date", "received", "registration_date"],
    "closed_date": ["closed date", "closed_date"],
    "complaints": ["complaints", "complaint count", "complaint_count", "count", "total complaints"],
    "escalation": ["escalation level", "escalation"],
    "priority": ["priority"],
}


class ColumnMapper:
    """Map logical fields to actual column names in processed rows."""

    def __init__(self, columns: list[str]) -> None:
        self._columns = columns
        self._lookup = {column.lower().strip(): column for column in columns}

    def resolve(self, field: str) -> str | None:
        for alias in COLUMN_ALIASES.get(field, [field]):
            column = self._lookup.get(alias.lower().strip())
            if column:
                return column
        return None

    def value(self, row: dict[str, Any], field: str, default: Any = None) -> Any:
        column = self.resolve(field)
        if not column:
            return default
        return row.get(column, default)
