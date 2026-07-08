"""Execute compiled report rules against a dataset."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from statistics import mean
from typing import Any, Awaitable, Callable

from app.features.processing.rules.schemas import ExecutableRule, RuleType
from app.features.rules.engine.context import Dataset, ExecutionContext, Highlight
from app.features.rules.engine.executors.column_executor import ColumnRuleExecutor
from app.features.rules.engine.executors.filter_executor import FilterRuleExecutor
from app.features.rules.engine.executors.highlight_executor import HighlightRuleExecutor
from app.features.rules.engine.executors.sorting_executor import SortingRuleExecutor
from app.features.rules.engine.executors.top_executor import TopRuleExecutor
from app.features.processing.schemas import GroupAggregationConfig
from app.infrastructure.database.models import ConfigurableRuleModel

RuleHandler = Callable[[Dataset, dict[str, Any], ExecutionContext], Awaitable[Dataset]]


@dataclass
class RuleExecutionResult:
    dataset: Dataset
    highlights: list[Highlight] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    steps_applied: list[str] = field(default_factory=list)

    @property
    def row_count(self) -> int:
        return self.dataset.row_count

    @property
    def column_count(self) -> int:
        return self.dataset.column_count


class RuleEngine:
    """Generic rule executor — no report-specific branching."""

    def __init__(self) -> None:
        self._filter_executor = FilterRuleExecutor()
        self._sorting_executor = SortingRuleExecutor()
        self._top_executor = TopRuleExecutor()
        self._column_executor = ColumnRuleExecutor()
        self._highlight_executor = HighlightRuleExecutor()
        self._handlers: dict[RuleType, RuleHandler] = {
            RuleType.FILTER: self._execute_filter,
            RuleType.SORT: self._execute_sort,
            RuleType.TOP_N: self._execute_top_n,
            RuleType.HIDE_COLUMNS: self._execute_hide_columns,
            RuleType.COLUMN_ORDER: self._execute_column_order,
            RuleType.HIGHLIGHT_ROWS: self._execute_highlight_rows,
        }

    async def execute(self, dataset: Dataset, rules: list[ExecutableRule]) -> RuleExecutionResult:
        context = ExecutionContext(template_id="rule-engine")
        context.set_dataset(dataset.name, dataset)
        warnings: list[str] = []
        steps_applied: list[str] = []

        for rule in rules:
            if rule.type == RuleType.HIGHLIGHT_ROWS:
                await self._execute_highlight_rows(dataset, rule.params, context)
                steps_applied.append(rule.type.value)
                continue

            if rule.type == RuleType.GROUP:
                dataset = self._execute_group_sync(dataset, rule.params, warnings)
                steps_applied.append(rule.type.value)
                continue

            handler = self._handlers.get(rule.type)
            if handler is None:
                warnings.append(f"No handler registered for rule type: {rule.type}")
                continue

            dataset = await handler(dataset, rule.params, context)
            steps_applied.append(rule.type.value)

        warnings.extend(context.warnings)
        return RuleExecutionResult(
            dataset=dataset,
            highlights=context.highlights,
            warnings=warnings,
            steps_applied=steps_applied,
        )

    async def _execute_filter(self, dataset: Dataset, params: dict[str, Any], context: ExecutionContext) -> Dataset:
        rule = self._temp_rule(
            "filter",
            "include",
            {"logic": params.get("logic", "AND"), "conditions": params.get("conditions", [])},
        )
        return await self._filter_executor.execute(dataset, rule, context)

    async def _execute_sort(self, dataset: Dataset, params: dict[str, Any], context: ExecutionContext) -> Dataset:
        rule = self._temp_rule(
            "sorting",
            "single",
            {"column": params["column"], "direction": params.get("direction", "asc")},
        )
        return await self._sorting_executor.execute(dataset, rule, context)

    async def _execute_top_n(self, dataset: Dataset, params: dict[str, Any], context: ExecutionContext) -> Dataset:
        mode = params.get("mode", "top")
        rule_type = "top_n" if mode == "top" else "bottom_n"
        rule = self._temp_rule(
            "top",
            rule_type,
            {
                "n": params["count"],
                "by_column": params.get("byColumn", ""),
                "direction": params.get("direction", "desc"),
            },
        )
        return await self._top_executor.execute(dataset, rule, context)

    async def _execute_hide_columns(self, dataset: Dataset, params: dict[str, Any], context: ExecutionContext) -> Dataset:
        rule = self._temp_rule("column", "hide", {"columns": params.get("columns", [])})
        return await self._column_executor.execute(dataset, rule, context)

    async def _execute_column_order(self, dataset: Dataset, params: dict[str, Any], context: ExecutionContext) -> Dataset:
        rule = self._temp_rule("column", "reorder", {"order": params.get("order", [])})
        return await self._column_executor.execute(dataset, rule, context)

    async def _execute_highlight_rows(
        self,
        dataset: Dataset,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> Dataset:
        condition = params.get("condition", {})
        style = {
            "background_color": params.get("backgroundColor", "#FEF3C7"),
            "text_color": params.get("textColor"),
            "bold": params.get("bold", False),
        }
        rule = self._temp_rule(
            "highlight",
            "row",
            {"condition": {"logic": "AND", "conditions": [condition]}, "style": style},
        )
        return await self._highlight_executor.execute(dataset, rule, context)

    def _execute_group_sync(self, dataset: Dataset, params: dict[str, Any], warnings: list[str]) -> Dataset:
        group_by = params.get("groupBy", [])
        if not group_by:
            warnings.append("Grouping rule missing groupBy columns")
            return dataset

        missing = [column for column in group_by if column not in dataset.columns]
        if missing:
            warnings.append(f"Grouping columns not found: {', '.join(missing)}")
            return dataset

        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in dataset.rows:
            key = tuple(row.get(column) for column in group_by)
            grouped[key].append(row)

        aggregations = params.get("aggregations") or []
        if not aggregations:
            aggregations = [
                GroupAggregationConfig(column=group_by[0], function="count", outputColumn="count").model_dump(
                    by_alias=True
                )
            ]

        new_rows: list[dict[str, Any]] = []
        for key, rows in grouped.items():
            new_row = {column: key[index] for index, column in enumerate(group_by)}
            for aggregation in aggregations:
                output_column = aggregation.get("outputColumn") or f"{aggregation['column']}_{aggregation['function']}"
                new_row[output_column] = self._aggregate(rows, aggregation)
            new_rows.append(new_row)

        output_columns = list(group_by) + [
            aggregation.get("outputColumn") or f"{aggregation['column']}_{aggregation['function']}"
            for aggregation in aggregations
        ]
        return Dataset(columns=output_columns, rows=new_rows, name=dataset.name)

    def _aggregate(self, rows: list[dict[str, Any]], aggregation: dict[str, Any]) -> Any:
        column = aggregation["column"]
        function = aggregation["function"]
        values = [row.get(column) for row in rows]
        non_empty = [value for value in values if value is not None and value != ""]

        if function == "count":
            return len(rows)
        if function == "first":
            return values[0] if values else None
        if function == "last":
            return values[-1] if values else None
        if not non_empty:
            return None

        numeric = self._as_numbers(non_empty)
        if function == "sum":
            return sum(numeric)
        if function == "avg":
            return mean(numeric)
        if function == "min":
            return min(numeric)
        if function == "max":
            return max(numeric)
        return len(rows)

    @staticmethod
    def _as_numbers(values: list[Any]) -> list[float]:
        parsed: list[float] = []
        for value in values:
            try:
                parsed.append(float(value))
            except (TypeError, ValueError):
                continue
        return parsed or [0.0]

    @staticmethod
    def _temp_rule(category: str, rule_type: str, config: dict[str, Any]) -> ConfigurableRuleModel:
        return ConfigurableRuleModel(
            id="rule-engine-step",
            name="Rule Engine Step",
            category=category,
            rule_type=rule_type,
            config_json=json.dumps(config),
            priority=0,
            is_enabled=True,
            is_global=False,
        )
