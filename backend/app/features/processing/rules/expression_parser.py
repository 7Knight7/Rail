"""Parse simple rule expressions such as `Zone == South Central Railway`."""

from __future__ import annotations

import re
from typing import Any

from app.features.processing.rules.column_resolver import resolve_column

_EXPRESSION_PATTERN = re.compile(
    r"^\s*(?P<field>[A-Za-z][A-Za-z0-9_\s]*?)\s*(?P<operator>==|!=|>=|<=|>|<)\s*(?P<value>.+?)\s*$"
)

_OPERATOR_MAP = {
    "==": "equals",
    "!=": "not_equals",
    ">": "gt",
    "<": "lt",
    ">=": "gte",
    "<=": "lte",
}


def parse_expression(expression: str, columns: list[str]) -> dict[str, Any]:
    match = _EXPRESSION_PATTERN.match(expression)
    if not match:
        raise ValueError(f"Unsupported expression: {expression}")

    field = resolve_column(match.group("field").strip(), columns)
    operator = _OPERATOR_MAP[match.group("operator")]
    value = _parse_value(match.group("value").strip())

    return {"field": field, "operator": operator, "value": value}


def _parse_value(raw: str) -> Any:
    if raw.lower() in {"true", "false"}:
        return raw.lower() == "true"
    if re.fullmatch(r"-?\d+(\.\d+)?", raw):
        if "." in raw:
            return float(raw)
        return int(raw)
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    return raw
