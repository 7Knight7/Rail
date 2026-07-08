"""Resolve column identifiers from report configuration."""

from __future__ import annotations

import re

COLUMN_ALIASES: dict[str, str] = {
    "received": "Registration Date",
    "registration date": "Registration Date",
    "complaints": "Complaints",
    "zone": "Zone",
    "division": "Division",
    "train no": "Train No",
    "train": "Train No",
    "station": "Station",
    "status": "Current Status",
}


def column_letter_to_index(letter: str) -> int:
    normalized = letter.strip().upper()
    index = 0
    for char in normalized:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1


def resolve_column(identifier: str, columns: list[str]) -> str:
    if not identifier:
        return identifier

    if identifier in columns:
        return identifier

    alias = COLUMN_ALIASES.get(identifier.strip().lower())
    if alias and alias in columns:
        return alias

    if re.fullmatch(r"[A-Za-z]+", identifier) and len(identifier) <= 3:
        index = column_letter_to_index(identifier)
        if 0 <= index < len(columns):
            return columns[index]

    return identifier


def resolve_columns(identifiers: list[str], columns: list[str]) -> list[str]:
    return [resolve_column(identifier, columns) for identifier in identifiers]
