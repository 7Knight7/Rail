"""Home overview service — live operations center data."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.dashboard.service import DashboardService
from app.features.home.schemas import HomeActivityItem, HomeOverviewResponse, HomeReportStatus, HomeStatMetric
from app.features.outputs.service import OutputGenerationService, REPORT_TYPE_LABELS
from app.features.processing.rules.registry import REPORT_RULE_REGISTRY

REPORT_PATHS: dict[str, str] = {
    "merging": "/workflows/merging",
    "division": "/workflows/division",
    "train-no": "/workflows/train-no",
    "types": "/workflows/types",
    "scr-train": "/workflows/scr-train",
    "scr-station": "/workflows/scr-station",
}


class HomeOverviewService:
    def __init__(self, session: AsyncSession) -> None:
        self._outputs = OutputGenerationService(session)
        self._dashboard = DashboardService(session)

    async def get_overview(self) -> HomeOverviewResponse:
        generated = self._outputs.list_reports(sort_by="generatedAt", sort_order="desc")
        dashboard = await self._dashboard.load_overview()

        generated_ids_today = self._reports_generated_today(generated.reports)
        last_generated = generated.reports[0].generated_at if generated.reports else None

        open_cases = next((kpi.value for kpi in dashboard.kpis if kpi.title == "Open Cases"), "0")
        resolution_rate = next(
            (kpi.value for kpi in dashboard.kpis if kpi.title == "Resolution Rate"),
            "0%",
        )

        stats = [
            HomeStatMetric(
                title="Last Generated",
                value=self._format_time(last_generated) if last_generated else "Not yet",
                description="Most recent report output",
            ),
            HomeStatMetric(
                title="Reports Available",
                value=f"{len(REPORT_RULE_REGISTRY)} Reports",
                description="Configured report types",
            ),
            HomeStatMetric(
                title="Generated Today",
                value=str(len(generated_ids_today)),
                description="Reports generated today",
            ),
            HomeStatMetric(
                title="Open Cases",
                value=str(open_cases),
                description=f"Resolution rate {resolution_rate}",
            ),
        ]

        recent_activity = [
            HomeActivityItem(
                label=f"{report.report_name} generated",
                time=self._relative_time(report.generated_at),
            )
            for report in generated.reports[:6]
        ]
        if dashboard.recent_activity:
            for item in dashboard.recent_activity[:3]:
                recent_activity.append(HomeActivityItem(label=item.label, time=item.time))

        reports: list[HomeReportStatus] = []
        for report_id, rule_set in REPORT_RULE_REGISTRY.items():
            latest = next((r for r in generated.reports if r.report_id == report_id), None)
            generated_today = report_id in generated_ids_today
            reports.append(
                HomeReportStatus(
                    reportId=report_id,
                    name=rule_set.report_name,
                    path=REPORT_PATHS.get(report_id, f"/workflows/{report_id}"),
                    status="Generated" if generated_today else ("Ready" if latest else "Ready"),
                    generatedAt=latest.generated_at if latest else None,
                )
            )

        return HomeOverviewResponse(
            stats=stats,
            recentActivity=recent_activity[:8],
            reports=reports,
        )

    @staticmethod
    def _reports_generated_today(reports) -> set[str]:
        today = datetime.now(UTC).date()
        generated_today: set[str] = set()
        for report in reports:
            try:
                generated_date = datetime.fromisoformat(
                    report.generated_at.replace("Z", "+00:00")
                ).date()
            except ValueError:
                continue
            if generated_date == today:
                generated_today.add(report.report_id)
        return generated_today

    @staticmethod
    def _format_time(value: str | None) -> str:
        if not value:
            return "—"
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%b %d, %I:%M %p")
        except ValueError:
            return value

    @staticmethod
    def _relative_time(value: str | None) -> str:
        if not value:
            return "Just now"
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            delta = datetime.now(UTC) - parsed.astimezone(UTC)
            minutes = int(delta.total_seconds() // 60)
            if minutes < 1:
                return "Just now"
            if minutes < 60:
                return f"{minutes} min ago"
            hours = minutes // 60
            if hours < 24:
                return f"{hours} hr ago"
            return f"{hours // 24} day ago"
        except ValueError:
            return value
