"""Rule engine schemas — report-specific configuration, generic execution."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RuleType(StrEnum):
    FILTER = "filter"
    SORT = "sort"
    GROUP = "group"
    TOP_N = "top_n"
    HIDE_COLUMNS = "hide_columns"
    COLUMN_ORDER = "column_order"
    HIGHLIGHT_ROWS = "highlight_rows"


class ReportRulesConfig(BaseModel):
    """Declarative per-report rule configuration."""

    sort_by: str | None = Field(default=None, alias="sortBy")
    order: Literal["ASC", "DESC", "asc", "desc"] | None = None
    top_n: int | None = Field(default=None, alias="topN")
    top_n_mode: Literal["top", "bottom"] = Field(default="top", alias="topNMode")
    hide_columns: list[str] = Field(default_factory=list, alias="hideColumns")
    column_order: list[str] = Field(default_factory=list, alias="columnOrder")
    highlight_rows: str | list[str] | None = Field(default=None, alias="highlightRows")
    filters: list[str] | None = None
    group_by: list[str] | None = Field(default=None, alias="groupBy")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class ExecutableRule(BaseModel):
    type: RuleType
    params: dict[str, Any] = Field(default_factory=dict)
    order: int = 0


class ReportRuleSet(BaseModel):
    report_id: str = Field(alias="reportId")
    report_name: str = Field(alias="reportName")
    rules: ReportRulesConfig

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class ReportRuleSetResponse(BaseModel):
    reports: list[ReportRuleSet]

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)
