"""Compile report rule configuration into executable rule steps."""

from __future__ import annotations

from app.features.processing.rules.column_resolver import resolve_column, resolve_columns
from app.features.processing.rules.expression_parser import parse_expression
from app.features.processing.rules.schemas import ExecutableRule, ReportRulesConfig, RuleType

RULE_PIPELINE_ORDER: dict[RuleType, int] = {
    RuleType.FILTER: 10,
    RuleType.SORT: 20,
    RuleType.GROUP: 30,
    RuleType.TOP_N: 40,
    RuleType.HIDE_COLUMNS: 50,
    RuleType.COLUMN_ORDER: 55,
    RuleType.HIGHLIGHT_ROWS: 60,
}


class RuleCompiler:
    """Translate declarative report configuration into generic executable rules."""

    def compile(self, config: ReportRulesConfig, columns: list[str]) -> list[ExecutableRule]:
        rules: list[ExecutableRule] = []

        if config.filters:
            for expression in config.filters:
                condition = parse_expression(expression, columns)
                rules.append(
                    ExecutableRule(
                        type=RuleType.FILTER,
                        params={"logic": "AND", "conditions": [condition]},
                        order=RULE_PIPELINE_ORDER[RuleType.FILTER],
                    )
                )

        if config.group_by:
            rules.append(
                ExecutableRule(
                    type=RuleType.GROUP,
                    params={
                        "groupBy": resolve_columns(config.group_by, columns),
                        "aggregations": [],
                    },
                    order=RULE_PIPELINE_ORDER[RuleType.GROUP],
                )
            )

        sort_column = resolve_column(config.sort_by, columns) if config.sort_by else None
        if sort_column:
            direction = (config.order or "DESC").lower()
            rules.append(
                ExecutableRule(
                    type=RuleType.SORT,
                    params={"column": sort_column, "direction": direction},
                    order=RULE_PIPELINE_ORDER[RuleType.SORT],
                )
            )

        if config.top_n:
            rules.append(
                ExecutableRule(
                    type=RuleType.TOP_N,
                    params={
                        "count": config.top_n,
                        "mode": config.top_n_mode,
                        "byColumn": sort_column or resolve_column(config.sort_by or "", columns),
                        "direction": (config.order or "DESC").lower(),
                    },
                    order=RULE_PIPELINE_ORDER[RuleType.TOP_N],
                )
            )

        if config.hide_columns:
            rules.append(
                ExecutableRule(
                    type=RuleType.HIDE_COLUMNS,
                    params={"columns": resolve_columns(config.hide_columns, columns)},
                    order=RULE_PIPELINE_ORDER[RuleType.HIDE_COLUMNS],
                )
            )

        if config.column_order:
            rules.append(
                ExecutableRule(
                    type=RuleType.COLUMN_ORDER,
                    params={"order": resolve_columns(config.column_order, columns)},
                    order=RULE_PIPELINE_ORDER[RuleType.COLUMN_ORDER],
                )
            )

        if config.highlight_rows:
            expressions = (
                [config.highlight_rows]
                if isinstance(config.highlight_rows, str)
                else list(config.highlight_rows)
            )
            for index, expression in enumerate(expressions):
                condition = parse_expression(expression, columns)
                rules.append(
                    ExecutableRule(
                        type=RuleType.HIGHLIGHT_ROWS,
                        params={
                            "condition": condition,
                            "backgroundColor": "#FEF3C7",
                            "priority": index + 1,
                        },
                        order=RULE_PIPELINE_ORDER[RuleType.HIGHLIGHT_ROWS] + index,
                    )
                )

        return sorted(rules, key=lambda rule: rule.order)
