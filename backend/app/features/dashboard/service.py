"""Dashboard data service — orchestrates processed reports into dashboard JSON."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.dashboard.aggregator import DashboardAggregator
from app.features.dashboard.schemas import (
    DashboardGenerateRequest,
    DashboardResponse,
    ProcessedReportInput,
)
from app.features.processing.rules.registry import REPORT_RULE_REGISTRY
from app.features.processing.schemas import ProcessDatasetRequest, ProcessDatasetResponse
from app.features.processing.service import ReportProcessingService


DEFAULT_REPORT_IDS = list(REPORT_RULE_REGISTRY.keys())


class DashboardService:
    """Generate dashboard KPIs, charts, analytics, and activity from processed reports."""

    def __init__(self, session: AsyncSession) -> None:
        self._processing_service = ReportProcessingService(session)
        self._aggregator = DashboardAggregator()

    def generate(self, request: DashboardGenerateRequest) -> DashboardResponse:
        return self._aggregator.build(request.reports, period=request.period)

    async def load_overview(
        self,
        report_ids: list[str] | None = None,
        period: str | None = None,
    ) -> DashboardResponse:
        """Process registered reports and build dashboard data."""
        selected_ids = report_ids or DEFAULT_REPORT_IDS
        processed_reports: list[ProcessedReportInput] = []

        for report_id in selected_ids:
            try:
                result = await self._processing_service.process(
                    ProcessDatasetRequest(reportId=report_id)
                )
            except Exception:
                continue

            rule_set = REPORT_RULE_REGISTRY.get(report_id)
            processed_reports.append(
                ProcessedReportInput(
                    reportId=report_id,
                    reportName=rule_set.report_name if rule_set else report_id,
                    processedAt=datetime.now(UTC).isoformat(),
                    data=result,
                )
            )

        return self._aggregator.build(processed_reports, period=period)

    @staticmethod
    def to_processed_report_input(
        report_id: str,
        report_name: str | None,
        data: ProcessDatasetResponse,
        processed_at: str | None = None,
    ) -> ProcessedReportInput:
        return ProcessedReportInput(
            reportId=report_id,
            reportName=report_name,
            processedAt=processed_at or datetime.now(UTC).isoformat(),
            data=data,
        )
