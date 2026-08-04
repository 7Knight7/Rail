"""Output column catalog for Report 14 Watering Complaints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Report14Column:
    id: str
    label: str
    required: bool = False
    default_visible: bool = True
    group: str = "shared"
    group_title: str = "Shared"


REPORT14_OUTPUT_COLUMNS: tuple[Report14Column, ...] = (
    Report14Column("sno", "S.No.", required=True, group="shared", group_title="Shared"),
    Report14Column(
        "station",
        "Station",
        required=True,
        group="shared",
        group_title="Shared",
    ),
    Report14Column(
        "prev_opening_balance",
        "Prev Opening Balance",
        group="previous",
        group_title="Previous Watering Point",
    ),
    Report14Column(
        "prev_received",
        "Prev Received",
        required=True,
        group="previous",
        group_title="Previous Watering Point",
    ),
    Report14Column(
        "prev_pct_share",
        "Prev % Share",
        group="previous",
        group_title="Previous Watering Point",
    ),
    Report14Column(
        "prev_closed",
        "Prev Closed",
        group="previous",
        group_title="Previous Watering Point",
    ),
    Report14Column(
        "prev_closing_balance",
        "Prev Closing Balance",
        group="previous",
        group_title="Previous Watering Point",
    ),
    Report14Column(
        "prev_pct_disposal",
        "Prev % Disposal",
        group="previous",
        group_title="Previous Watering Point",
    ),
    Report14Column(
        "up_opening_balance",
        "Up Opening Balance",
        group="upcoming",
        group_title="Upcoming Watering Point",
    ),
    Report14Column(
        "up_received",
        "Up Received",
        required=True,
        group="upcoming",
        group_title="Upcoming Watering Point",
    ),
    Report14Column(
        "up_pct_share",
        "Up % Share",
        group="upcoming",
        group_title="Upcoming Watering Point",
    ),
    Report14Column(
        "up_closed",
        "Up Closed",
        group="upcoming",
        group_title="Upcoming Watering Point",
    ),
    Report14Column(
        "up_closing_balance",
        "Up Closing Balance",
        group="upcoming",
        group_title="Upcoming Watering Point",
    ),
    Report14Column(
        "up_pct_disposal",
        "Up % Disposal",
        group="upcoming",
        group_title="Upcoming Watering Point",
    ),
)

REPORT14_COLUMN_BY_ID: dict[str, Report14Column] = {
    c.id: c for c in REPORT14_OUTPUT_COLUMNS
}
REPORT14_LABEL_BY_ID: dict[str, str] = {c.id: c.label for c in REPORT14_OUTPUT_COLUMNS}
REPORT14_ID_BY_LABEL: dict[str, str] = {c.label: c.id for c in REPORT14_OUTPUT_COLUMNS}


def report14_default_ids() -> list[str]:
    return [c.id for c in REPORT14_OUTPUT_COLUMNS if c.default_visible]


def report14_allowed_ids() -> frozenset[str]:
    return frozenset(REPORT14_COLUMN_BY_ID.keys())


def report14_catalog_entries() -> list[dict[str, object]]:
    return [
        {
            "id": c.id,
            "label": c.label,
            "required": c.required,
            "default_visible": c.default_visible,
            "group": c.group,
            "group_title": c.group_title,
        }
        for c in REPORT14_OUTPUT_COLUMNS
    ]


def report14_labels(ids: Iterable[str]) -> list[str]:
    return [REPORT14_LABEL_BY_ID[i] for i in ids if i in REPORT14_LABEL_BY_ID]


def validate_selected_report14_fields(selected: Iterable[str]) -> list[str]:
    allowed = report14_allowed_ids()
    ordered: list[str] = []
    seen: set[str] = set()
    for item in selected:
        key = str(item).strip()
        if not key or key in seen or key not in allowed:
            continue
        seen.add(key)
        ordered.append(key)
    # Always include required columns even if omitted.
    for col in REPORT14_OUTPUT_COLUMNS:
        if col.required and col.id not in seen:
            ordered.insert(0 if col.id == "sno" else len(ordered), col.id)
            seen.add(col.id)
    # Keep sno first, station second when present.
    fixed: list[str] = []
    if "sno" in seen:
        fixed.append("sno")
    if "station" in seen:
        fixed.append("station")
    for key in ordered:
        if key not in fixed:
            fixed.append(key)
    return fixed if fixed else report14_default_ids()
