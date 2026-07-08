"""Curated filter definitions for MIS Report 1 (refine after live discovery)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal


FilterFieldType = Literal["text", "date", "select", "radio", "checkbox"]


@dataclass(frozen=True)
class FilterFieldDefinition:
    """Describes a single report filter field to populate."""

    name: str
    selector: str
    field_type: FilterFieldType
    value: str
    required: bool = True
    label: str = ""


def resolve_filter_value(value_key: str, date_format: str = "%d/%m/%Y") -> str:
    """Resolve symbolic filter values such as 'today'."""
    today = datetime.now().strftime(date_format)
    if value_key == "today":
        return today
    if value_key == "today_range":
        return "Current Day"
    return value_key


def resolve_field_value(field: FilterFieldDefinition, date_format: str = "%d/%m/%Y") -> str:
    return resolve_filter_value(field.value, date_format=date_format)


def _infer_field_type(discovered: dict[str, Any]) -> FilterFieldType:
    tag = str(discovered.get("tag", "")).lower()
    input_type = str(discovered.get("field_type") or discovered.get("type") or "").lower()
    if tag == "select":
        return "select"
    if tag == "textarea":
        return "text"
    if input_type == "checkbox":
        return "checkbox"
    if input_type == "radio":
        return "radio"
    if input_type == "date" or "date" in str(discovered.get("field_name", "")).lower():
        return "date"
    return "text"


def normalize_discovered_field(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize discovery output to stable field keys."""
    field_id = raw.get("field_id") or raw.get("id") or ""
    field_name = raw.get("field_name") or raw.get("name") or ""
    field_type = raw.get("field_type") or raw.get("type") or raw.get("tag") or ""
    field_label = raw.get("field_label") or raw.get("label") or ""
    selector = raw.get("selector") or (f"#{field_id}" if field_id else "")
    if not selector and field_name:
        selector = f"[name='{field_name}']"
    current_value = raw.get("current_value")
    if current_value is None:
        current_value = raw.get("value") or ""
    return {
        "tag": raw.get("tag", ""),
        "field_id": field_id,
        "field_name": field_name,
        "field_type": field_type,
        "field_label": field_label,
        "selector": selector,
        "current_value": current_value,
        "required": bool(raw.get("required", False)),
        "options": raw.get("options") or [],
    }


def build_filters_from_discovery(
    discovered: list[dict[str, Any]],
    slug: str = "report1",
) -> list[FilterFieldDefinition]:
    """Build filter definitions from live discovery, with date/today defaults."""
    if slug != "report1":
        return []

    normalized = [normalize_discovered_field(field) for field in discovered]
    filters: list[FilterFieldDefinition] = []
    seen: set[str] = set()
    has_date_range = any(field.get("field_id") == "dateRange" for field in normalized)

    for field in normalized:
        tag = str(field.get("tag", "")).lower()
        if tag == "button" or not field.get("selector"):
            continue

        field_id = str(field.get("field_id") or "")
        if has_date_range and field_id in {"fromDate", "toDate"}:
            continue

        field_label = str(field.get("field_label") or "").strip()
        field_name = str(field.get("field_name") or field_id or "").strip()
        label_lower = field_label.lower()
        name_lower = field_name.lower()
        logical_name = field_name or field_id or field_label.replace(" ", "_").lower()
        if not logical_name or logical_name in seen:
            continue
        seen.add(logical_name)

        field_type = _infer_field_type(field)
        selector = str(field["selector"])
        current_value = str(field.get("current_value") or "")

        if field_id == "dateRange" or (field_type == "select" and "date range" in label_lower):
            value = "today_range"
            required = True
        elif field_type in ("text", "date") and any(
            token in label_lower or token in name_lower
            for token in ("from date", "fromdate", "frmdate", "from_date")
        ):
            value = "today"
            required = True
        elif field_type in ("text", "date") and any(
            token in label_lower or token in name_lower
            for token in ("to date", "todate", "to_date")
        ):
            value = "today"
            required = True
        elif field.get("required"):
            value = current_value
            required = True
            if not value:
                continue
        else:
            continue

        filters.append(
            FilterFieldDefinition(
                name=logical_name,
                selector=selector,
                field_type=field_type,
                value=value,
                required=required,
                label=field_label,
            )
        )

    return filters if filters else list(REPORT_1_FILTERS)


# Report 1 renders filters on the main admin page (not an iframe).
REPORT_1_FILTERS: list[FilterFieldDefinition] = [
    FilterFieldDefinition(
        name="dateRange",
        selector=(
            "select[name*='dateRange'], select[id*='dateRange'], "
            "select[name*='DateRange'], select[id*='DateRange'], "
            "select[name*='date'], select[id*='date']"
        ),
        field_type="select",
        value="today_range",
        required=True,
        label="Date Range",
    ),
]


def filters_for_report(slug: str = "report1") -> list[FilterFieldDefinition]:
    if slug == "report1":
        return list(REPORT_1_FILTERS)
    return []


def applied_filter_records(
    fields: list[FilterFieldDefinition],
    values: dict[str, str],
) -> list[dict[str, Any]]:
    return [
        {
            "name": field.name,
            "value": values.get(field.name, ""),
            "label": field.label or field.name,
        }
        for field in fields
    ]
