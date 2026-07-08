"""Generic report processing facade backed by the rule engine."""

from __future__ import annotations

from app.features.processing.rules.compiler import RULE_PIPELINE_ORDER, RuleCompiler
from app.features.processing.rules.column_resolver import resolve_column, resolve_columns
from app.features.processing.rules.expression_parser import parse_expression
from app.features.processing.rules.rule_engine import RuleEngine, RuleExecutionResult
from app.features.processing.rules.schemas import ExecutableRule, ReportRulesConfig, RuleType
from app.features.processing.schemas import FilterConditionConfig, ReportConfiguration
from app.features.rules.engine.context import Dataset


class ReportProcessingEngine:
    """Compile configuration into rules and execute them without report-specific logic."""

    def __init__(self) -> None:
        self._compiler = RuleCompiler()
        self._rule_engine = RuleEngine()

    async def process_rules(self, dataset: Dataset, rules: list[ExecutableRule]) -> RuleExecutionResult:
        return await self._rule_engine.execute(dataset, rules)

    async def process(self, dataset: Dataset, configuration: ReportConfiguration) -> RuleExecutionResult:
        legacy_rules = self._compile_legacy(configuration, dataset.columns)
        return await self._rule_engine.execute(dataset, legacy_rules)

    async def process_report_config(self, dataset: Dataset, config: ReportRulesConfig) -> RuleExecutionResult:
        rules = self._compiler.compile(config, dataset.columns)
        return await self._rule_engine.execute(dataset, rules)

    def _compile_legacy(self, configuration: ReportConfiguration, columns: list[str]) -> list[ExecutableRule]:
        sort_column = (
            resolve_column(configuration.sorting[0].column, columns) if configuration.sorting else None
        )
        shorthand = ReportRulesConfig(
            sortBy=sort_column,
            order=configuration.sorting[0].direction.upper() if configuration.sorting else None,
            topN=configuration.top_n.count if configuration.top_n and configuration.top_n.enabled else None,
            topNMode=configuration.top_n.mode if configuration.top_n else "top",
            hideColumns=configuration.hidden_columns,
            columnOrder=configuration.column_order,
        )

        rules = self._compiler.compile(shorthand, columns)

        if configuration.filters:
            rules.append(
                ExecutableRule(
                    type=RuleType.FILTER,
                    params={
                        "logic": configuration.filters[0].logic,
                        "conditions": [
                            self._filter_condition_to_dict(item, columns) for item in configuration.filters
                        ],
                    },
                    order=RULE_PIPELINE_ORDER[RuleType.FILTER],
                )
            )

        if configuration.grouping and configuration.grouping.enabled:
            rules.append(
                ExecutableRule(
                    type=RuleType.GROUP,
                    params={
                        "groupBy": resolve_columns(configuration.grouping.group_by, columns),
                        "aggregations": [
                            aggregation.model_dump(by_alias=True)
                            for aggregation in configuration.grouping.aggregations
                        ],
                    },
                    order=RULE_PIPELINE_ORDER[RuleType.GROUP],
                )
            )

        if configuration.highlights:
            for index, item in enumerate(configuration.highlights):
                if not item.column or item.value is None:
                    continue
                expression = self._filter_to_expression(item.column, item.operator, item.value, None)
                rules.append(
                    ExecutableRule(
                        type=RuleType.HIGHLIGHT_ROWS,
                        params={
                            "condition": parse_expression(expression, columns),
                            "backgroundColor": item.background_color or "#FEF3C7",
                            "textColor": item.text_color,
                            "bold": item.bold,
                            "priority": index + 1,
                        },
                        order=RULE_PIPELINE_ORDER[RuleType.HIGHLIGHT_ROWS] + index,
                    )
                )

        return sorted(rules, key=lambda rule: rule.order)

    @staticmethod
    def _filter_condition_to_dict(item: FilterConditionConfig, columns: list[str]) -> dict:
        operator_map = {
            "equals": "equals",
            "eq": "equals",
            "on": "equals",
            "not_equals": "not_equals",
            "contains": "contains",
            "starts_with": "starts_with",
            "ends_with": "ends_with",
            "gt": "gt",
            "lt": "lt",
            "gte": "gte",
            "lte": "lte",
            "before": "lt",
            "after": "gt",
            "true": "equals",
            "false": "equals",
            "between": "between",
        }
        operator = operator_map.get(item.operator, item.operator)
        value = item.value
        if item.operator == "true":
            value = True
        elif item.operator == "false":
            value = False
        elif operator == "between" and item.value_to is not None:
            value = [item.value, item.value_to]

        return {
            "field": resolve_column(item.column, columns),
            "operator": operator,
            "value": value,
        }

    @staticmethod
    def _filter_to_expression(column: str, operator: str, value, value_to) -> str:
        if operator == "between" and value_to is not None:
            return f"{column} >= {value} AND {column} <= {value_to}"
        if operator in {"equals", "eq", "on"}:
            return f'{column} == "{value}"'
        if operator == "not_equals":
            return f'{column} != "{value}"'
        if operator == "contains":
            return f'{column} == "{value}"'
        if operator == "gt":
            return f"{column} > {value}"
        if operator == "lt":
            return f"{column} < {value}"
        if operator == "gte":
            return f"{column} >= {value}"
        if operator == "lte":
            return f"{column} <= {value}"
        return f"{column} == \"{value}\""
