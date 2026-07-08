"""Home overview schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HomeStatMetric(BaseModel):
    title: str
    value: str
    description: str

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class HomeActivityItem(BaseModel):
    label: str
    time: str

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class HomeReportStatus(BaseModel):
    report_id: str = Field(alias="reportId")
    name: str
    path: str
    status: str
    generated_at: str | None = Field(default=None, alias="generatedAt")

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class HomeOverviewResponse(BaseModel):
    stats: list[HomeStatMetric] = Field(default_factory=list)
    recent_activity: list[HomeActivityItem] = Field(default_factory=list, alias="recentActivity")
    reports: list[HomeReportStatus] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)
