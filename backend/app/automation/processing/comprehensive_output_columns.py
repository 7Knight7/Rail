"""Output column definitions for Report 10-13 (Comprehensive Reports).

All four sections share the same available columns from the Division Wise view.
"""

from __future__ import annotations

COMPREHENSIVE_COLUMN_IDS: list[str] = [
    "sno",
    "division",
    "opening_balance",
    "received",
    "share_percent",
    "closed",
    "closing_balance",
    "disposal_percent",
    "avg_disposal_time",
    "avg_rating",
    "avg_pendency_time",
]

COMPREHENSIVE_COLUMN_LABELS: dict[str, str] = {
    "sno": "S.No.",
    "division": "Division",
    "opening_balance": "Opening Balance",
    "received": "Received",
    "share_percent": "% Share",
    "closed": "Closed",
    "closing_balance": "Closing Balance",
    "disposal_percent": "% Disposal",
    "avg_disposal_time": "Avg. Disposal Time",
    "avg_rating": "Avg. Rating",
    "avg_pendency_time": "Avg. Pendency Time",
}

COMPREHENSIVE_HEADER_ALIASES: dict[str, str] = {
    "S.No.": "sno",
    "S.No": "sno",
    "SNo": "sno",
    "Sno": "sno",
    "Sl.No.": "sno",
    "Sl No": "sno",
    "Division": "division",
    "Organisation": "division",
    "Opening Balance": "opening_balance",
    "Opening": "opening_balance",
    "Received": "received",
    "% Share": "share_percent",
    "Share %": "share_percent",
    "Closed": "closed",
    "Closing Balance": "closing_balance",
    "Closing": "closing_balance",
    "% Disposal": "disposal_percent",
    "Disposal %": "disposal_percent",
    "Avg. Disposal Time": "avg_disposal_time",
    "Avg Disposal Time": "avg_disposal_time",
    "Avg. Rating": "avg_rating",
    "Avg Rating": "avg_rating",
    "Avg. Pendency Time": "avg_pendency_time",
    "Avg Pendency Time": "avg_pendency_time",
}

ADDITIVE_COLUMNS: set[str] = {
    "opening_balance",
    "received",
    "closed",
    "closing_balance",
}

NON_ADDITIVE_COLUMNS: set[str] = {
    "disposal_percent",
    "avg_disposal_time",
    "avg_rating",
    "avg_pendency_time",
}


def normalize_header_to_column_id(header: str) -> str | None:
    """Map a raw header string to a canonical column ID."""
    header_clean = header.strip()
    if header_clean in COMPREHENSIVE_HEADER_ALIASES:
        return COMPREHENSIVE_HEADER_ALIASES[header_clean]
    for alias, col_id in COMPREHENSIVE_HEADER_ALIASES.items():
        if alias.lower() == header_clean.lower():
            return col_id
    return None


def default_column_ids() -> list[str]:
    """Return the default column IDs for comprehensive reports."""
    return list(COMPREHENSIVE_COLUMN_IDS)


def column_labels(column_ids: list[str]) -> list[str]:
    """Return display labels for given column IDs."""
    return [COMPREHENSIVE_COLUMN_LABELS.get(cid, cid) for cid in column_ids]
