"""Output generation schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.features.dashboard.schemas import DashboardResponse
from app.features.processing.rules.schemas import ReportRulesConfig
from app.features.processing.schemas import ProcessDatasetResponse, ReportConfiguration


class GenerateOutputsRequest(BaseModel):
    """Generate final Excel, PDF, and dashboard JSON from a processed dataset."""

    report_id: str = Field(alias="reportId")
    report_name: str | None = Field(default=None, alias="reportName")
    processed: ProcessDatasetResponse | None = None
    configuration: ReportConfiguration | None = None
    rules: ReportRulesConfig | None = None
    include_excel: bool = Field(default=True, alias="includeExcel")
    include_pdf: bool = Field(default=True, alias="includePdf")
    include_csv: bool = Field(default=False, alias="includeCsv")
    include_dashboard: bool = Field(default=True, alias="includeDashboard")
    period: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class OutputArtifact(BaseModel):
    format: Literal["excel", "pdf", "csv", "dashboard_json"]
    filename: str
    path: str
    download_url: str = Field(alias="downloadUrl")
    size: int

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class GenerateOutputsResponse(BaseModel):
    batch_id: str = Field(alias="batchId")
    report_id: str = Field(alias="reportId")
    report_name: str = Field(alias="reportName")
    generated_at: str = Field(alias="generatedAt")
    processed: ProcessDatasetResponse
    dashboard: DashboardResponse | None = None
    artifacts: list[OutputArtifact] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class GeneratedReportItem(BaseModel):
    batch_id: str = Field(alias="batchId")
    report_id: str = Field(alias="reportId")
    report_name: str = Field(alias="reportName")
    report_type: str = Field(alias="reportType")
    generated_at: str = Field(alias="generatedAt")
    status: Literal["completed", "partial", "failed"] = "completed"
    excel_download_url: str | None = Field(default=None, alias="excelDownloadUrl")
    pdf_download_url: str | None = Field(default=None, alias="pdfDownloadUrl")
    excel_size: int | None = Field(default=None, alias="excelSize")
    pdf_size: int | None = Field(default=None, alias="pdfSize")

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class GeneratedReportListResponse(BaseModel):
    reports: list[GeneratedReportItem] = Field(default_factory=list)
    total: int = 0

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)
