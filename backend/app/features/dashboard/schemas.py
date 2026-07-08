"""Dashboard data service schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.features.processing.schemas import ProcessDatasetResponse


class ProcessedReportInput(BaseModel):
    """A single processed report payload used as dashboard input."""

    report_id: str = Field(alias="reportId")
    report_name: str | None = Field(default=None, alias="reportName")
    processed_at: str | None = Field(default=None, alias="processedAt")
    data: ProcessDatasetResponse

    model_config = ConfigDict(populate_by_name=True)


class DashboardGenerateRequest(BaseModel):
    reports: list[ProcessedReportInput] = Field(default_factory=list)
    period: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class DashboardKpi(BaseModel):
    title: str
    value: str | int | float
    subtitle: str | None = None

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class ChartDataPoint(BaseModel):
    label: str
    value: float
    bar_width: float = Field(alias="barWidth")

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class ChartSection(BaseModel):
    title: str
    items: list[ChartDataPoint] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class FeedbackMetric(BaseModel):
    label: str
    value: str
    color: str | None = None

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class AnalyticsRow(BaseModel):
    label: str
    value: str

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class RecentActivityItem(BaseModel):
    label: str
    time: str
    report_id: str | None = Field(default=None, alias="reportId")

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class DashboardAnalytics(BaseModel):
    feedback: list[FeedbackMetric] = Field(default_factory=list)
    resolution: list[AnalyticsRow] = Field(default_factory=list)
    observations: list[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class DashboardCharts(BaseModel):
    complaint_trends: ChartSection = Field(alias="complaintTrends")
    complaint_categories: ChartSection = Field(alias="complaintCategories")
    top_zones: ChartSection = Field(alias="topZones")
    top_divisions: ChartSection = Field(alias="topDivisions")
    top_trains: ChartSection = Field(alias="topTrains")

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class DashboardResponse(BaseModel):
    generated_at: str = Field(alias="generatedAt")
    period: str = ""
    kpis: list[DashboardKpi] = Field(default_factory=list)
    charts: DashboardCharts
    analytics: DashboardAnalytics
    recent_activity: list[RecentActivityItem] = Field(default_factory=list, alias="recentActivity")
    source_reports: list[str] = Field(default_factory=list, alias="sourceReports")
    row_count: int = Field(default=0, alias="rowCount")

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class DashboardOverviewQuery(BaseModel):
    report_ids: list[str] | None = Field(default=None, alias="reportIds")

    model_config = ConfigDict(populate_by_name=True)
