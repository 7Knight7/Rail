"""Convert ingested datasets into the rules engine tabular format."""

from __future__ import annotations

from typing import Any

from app.core.spreadsheet.excel_reader import ExcelDataset
from app.core.spreadsheet.metadata_service import DatasetWithMetadata
from app.features.processing.schemas import FilterConditionConfig
from app.features.rules.engine.context import Dataset


def dataset_from_excel(excel_dataset: ExcelDataset) -> Dataset:
    columns = [column.name for column in excel_dataset.columns]
    rows = [
        {
            columns[index]: row[index] if index < len(row) else None
            for index in range(len(columns))
        }
        for row in excel_dataset.rows
    ]
    return Dataset(columns=columns, rows=rows, name="original")


def dataset_from_split(dataset_with_metadata: DatasetWithMetadata) -> Dataset:
    columns = [column.name for column in dataset_with_metadata.metadata.columns]
    rows = [
        {
            columns[index]: row[index] if index < len(row) else None
            for index in range(len(columns))
        }
        for row in dataset_with_metadata.rows
    ]
    return Dataset(columns=columns, rows=rows, name="original")


def map_filter_operator(operator: str) -> str:
    mapping = {
        "eq": "equals",
        "equals": "equals",
        "not_equals": "not_equals",
        "contains": "contains",
        "starts_with": "starts_with",
        "ends_with": "ends_with",
        "gt": "gt",
        "lt": "lt",
        "gte": "gte",
        "lte": "lte",
        "on": "equals",
        "before": "lt",
        "after": "gt",
        "between": "between",
        "true": "equals",
        "false": "equals",
        "is_null": "is_null",
        "is_not_null": "is_not_null",
    }
    return mapping.get(operator, operator)


def build_filter_condition(condition: FilterConditionConfig) -> dict[str, Any]:
    operator = map_filter_operator(condition.operator)

    if condition.operator == "between":
        value = [condition.value, condition.value_to]
    elif condition.operator == "true":
        value = True
    elif condition.operator == "false":
        value = False
    else:
        value = condition.value

    return {
        "field": condition.column,
        "operator": operator,
        "value": value,
    }


def build_filter_groups(filters: list[FilterConditionConfig]) -> list[dict[str, Any]]:
    if not filters:
        return []

    groups: list[dict[str, Any]] = []
    current_logic = filters[0].logic
    current_conditions: list[dict[str, Any]] = []

    for index, item in enumerate(filters):
        current_conditions.append(build_filter_condition(item))

        next_logic = filters[index + 1].logic if index + 1 < len(filters) else None
        if next_logic != current_logic or index == len(filters) - 1:
            groups.append({"logic": current_logic, "conditions": current_conditions})
            current_logic = next_logic or "AND"
            current_conditions = []

    return groups
