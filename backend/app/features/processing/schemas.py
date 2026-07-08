"""Schemas for generic report processing configuration."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.features.processing.rules.schemas import ReportRulesConfig


class FilterConditionConfig(BaseModel):
    column: str
    operator: str
    value: Any = None
    value_to: Any = Field(default=None, alias="valueTo")
    logic: Literal["AND", "OR"] = "AND"

    model_config = ConfigDict(populate_by_name=True)


class SortingConfig(BaseModel):
    column: str
    direction: Literal["asc", "desc"] = "asc"
    priority: int = 1


class TopNConfig(BaseModel):
    enabled: bool = False
    mode: Literal["top", "bottom"] = "top"
    count: int = Field(default=10, ge=1)
    by_column: str = Field(default="", alias="byColumn")
    direction: Literal["asc", "desc"] | None = None

    model_config = ConfigDict(populate_by_name=True)


class GroupAggregationConfig(BaseModel):
    column: str
    function: Literal["count", "sum", "avg", "min", "max", "first", "last"] = "count"
    output_column: str | None = Field(default=None, alias="outputColumn")

    model_config = ConfigDict(populate_by_name=True)


class GroupingConfig(BaseModel):
    enabled: bool = False
    group_by: list[str] = Field(default_factory=list, alias="groupBy")
    aggregations: list[GroupAggregationConfig] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class HighlightConfig(BaseModel):
    column: str | None = None
    scope: Literal["cell", "row", "column"] = "row"
    operator: str = "equals"
    value: Any = None
    background_color: str = Field(default="#FEF3C7", alias="backgroundColor")
    text_color: str | None = Field(default=None, alias="textColor")
    bold: bool = False
    priority: int = 1

    model_config = ConfigDict(populate_by_name=True)


class ReportConfiguration(BaseModel):
    """Generic processing configuration — no report-specific logic."""

    filters: list[FilterConditionConfig] = Field(default_factory=list)
    sorting: list[SortingConfig] = Field(default_factory=list)
    top_n: TopNConfig | None = Field(default=None, alias="topN")
    grouping: GroupingConfig | None = None
    hidden_columns: list[str] = Field(default_factory=list, alias="hiddenColumns")
    column_order: list[str] = Field(default_factory=list, alias="columnOrder")
    highlights: list[HighlightConfig] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class ProcessDatasetRequest(BaseModel):
    report_id: str | None = Field(default=None, alias="reportId")
    file_path: str | None = Field(default=None, alias="filePath")
    configuration: ReportConfiguration | None = None
    rules: ReportRulesConfig | None = None

    model_config = ConfigDict(populate_by_name=True)


class ProcessedColumn(BaseModel):
    name: str
    index: int

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class ProcessDatasetResponse(BaseModel):
    columns: list[ProcessedColumn]
    rows: list[dict[str, Any]]
    highlights: list[dict[str, Any]]
    row_count: int = Field(alias="rowCount")
    column_count: int = Field(alias="columnCount")
    steps_applied: list[str] = Field(alias="stepsApplied")
    warnings: list[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)
