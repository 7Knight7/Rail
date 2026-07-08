"""Aggregate processed report rows into dashboard KPIs, charts, and analytics."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, date, datetime, timedelta
from statistics import mean
from typing import Any

from app.features.dashboard.column_mapper import ColumnMapper
from app.features.dashboard.schemas import (
    AnalyticsRow,
    ChartDataPoint,
    ChartSection,
    DashboardAnalytics,
    DashboardCharts,
    DashboardKpi,
    DashboardResponse,
    FeedbackMetric,
    ProcessedReportInput,
    RecentActivityItem,
)
from app.features.summary.statistics_builder import StatisticsBuilder


class DashboardAggregator:
    """Build dashboard JSON from processed reports — all calculations happen here."""

    RESOLVED_STATUSES = {"resolved", "closed", "completed", "done"}
    PENDING_STATUSES = {"pending", "open", "in progress", "in_progress", "active"}
    POSITIVE_FEEDBACK = {"positive", "satisfied", "good", "excellent", "happy"}
    NEGATIVE_FEEDBACK = {"negative", "unsatisfied", "unsatisfactory", "poor", "bad"}

    def build(
        self,
        reports: list[ProcessedReportInput],
        period: str | None = None,
    ) -> DashboardResponse:
        merged_rows, columns, source_reports = self._merge_reports(reports)
        mapper = ColumnMapper(columns)
        report_period = period or datetime.now(UTC).strftime("%Y-%m-%d")

        if not merged_rows:
            return self._empty_dashboard(report_period, source_reports)

        stats = StatisticsBuilder().build(
            merged_rows,
            metadata={"report_period": report_period, "report_name": "Dashboard"},
            column_mapping={
                "status": mapper.resolve("status") or "status",
                "complaint_type": mapper.resolve("category") or "category",
                "division": mapper.resolve("division") or "division",
                "train_number": mapper.resolve("train") or "train",
                "complaint_count": mapper.resolve("complaints") or "complaints",
            },
        )

        kpis = self._build_kpis(merged_rows, mapper, stats)
        charts = self._build_charts(merged_rows, mapper, stats)
        analytics = self._build_analytics(merged_rows, mapper, stats)
        recent_activity = self._build_recent_activity(reports)

        return DashboardResponse(
            generatedAt=datetime.now(UTC).isoformat(),
            period=report_period,
            kpis=kpis,
            charts=charts,
            analytics=analytics,
            recentActivity=recent_activity,
            sourceReports=source_reports,
            rowCount=len(merged_rows),
        )

    def _merge_reports(
        self,
        reports: list[ProcessedReportInput],
    ) -> tuple[list[dict[str, Any]], list[str], list[str]]:
        rows: list[dict[str, Any]] = []
        columns: list[str] = []
        source_reports: list[str] = []
        seen_ids: set[str] = set()

        for report in reports:
            source_reports.append(report.report_id)
            for column in report.data.columns:
                if column.name not in columns:
                    columns.append(column.name)

            mapper = ColumnMapper([column.name for column in report.data.columns])
            id_column = mapper.resolve("grievance_id")

            for row in report.data.rows:
                if id_column:
                    grievance_id = str(row.get(id_column, ""))
                    if grievance_id and grievance_id in seen_ids:
                        continue
                    if grievance_id:
                        seen_ids.add(grievance_id)
                rows.append(row)

        return rows, columns, source_reports

    def _build_kpis(
        self,
        rows: list[dict[str, Any]],
        mapper: ColumnMapper,
        stats,
    ) -> list[DashboardKpi]:
        today = date.today()
        yesterday = today - timedelta(days=1)

        today_count = self._count_by_date(rows, mapper, today)
        yesterday_count = self._count_by_date(rows, mapper, yesterday)
        trend = self._format_trend(today_count, yesterday_count)

        open_cases = stats.pending_complaints
        resolution_rate = f"{stats.resolution_rate:.0f}%"
        feedback_score = self._average_feedback_score(rows, mapper)

        return [
            DashboardKpi(
                title="Today's Complaints",
                value=today_count or stats.total_complaints,
                subtitle=trend,
            ),
            DashboardKpi(
                title="Open Cases",
                value=open_cases,
                subtitle="Pending resolution",
            ),
            DashboardKpi(
                title="Resolution Rate",
                value=resolution_rate,
                subtitle="Across processed reports",
            ),
            DashboardKpi(
                title="Feedback Score",
                value=feedback_score,
                subtitle="Average rating",
            ),
        ]

    def _build_charts(
        self,
        rows: list[dict[str, Any]],
        mapper: ColumnMapper,
        stats,
    ) -> DashboardCharts:
        trends = self._group_by_weekday(rows, mapper, limit=5)
        categories = self._to_chart_items(
            [(item["name"], item["count"]) for item in stats.top_complaint_types[:5]],
            limit=5,
        )
        zones = self._aggregate_field(rows, mapper, "zone", limit=3)
        divisions = self._to_chart_items(
            [(item["name"], item["count"]) for item in stats.top_divisions[:3]],
            limit=3,
        )
        trains = self._to_chart_items(
            [(item["name"], item["count"]) for item in stats.top_trains[:3]],
            limit=3,
        )

        return DashboardCharts(
            complaintTrends=ChartSection(title="Complaint Trends", items=trends),
            complaintCategories=ChartSection(title="Complaint Categories", items=categories),
            topZones=ChartSection(title="Top Zones", items=zones),
            topDivisions=ChartSection(title="Top Divisions", items=divisions),
            topTrains=ChartSection(title="Top Trains", items=trains),
        )

    def _build_analytics(
        self,
        rows: list[dict[str, Any]],
        mapper: ColumnMapper,
        stats,
    ) -> DashboardAnalytics:
        feedback = self._feedback_breakdown(rows, mapper)
        resolution = self._resolution_rows(rows, mapper, stats)

        return DashboardAnalytics(
            feedback=feedback,
            resolution=resolution,
            observations=stats.key_observations,
        )

    def _build_recent_activity(self, reports: list[ProcessedReportInput]) -> list[RecentActivityItem]:
        activity: list[RecentActivityItem] = []

        for report in reports:
            label = f"{report.report_name or report.report_id} processed"
            time_label = self._relative_time(report.processed_at)
            activity.append(
                RecentActivityItem(
                    label=label,
                    time=time_label,
                    reportId=report.report_id,
                )
            )

        if reports:
            total_rows = sum(report.data.row_count for report in reports)
            activity.insert(
                0,
                RecentActivityItem(
                    label=f"{len(reports)} reports aggregated ({total_rows} rows)",
                    time="Just now",
                ),
            )

        return activity[:8]

    def _empty_dashboard(self, period: str, source_reports: list[str]) -> DashboardResponse:
        empty_chart = ChartSection(title="", items=[])
        return DashboardResponse(
            generatedAt=datetime.now(UTC).isoformat(),
            period=period,
            kpis=[
                DashboardKpi(title="Today's Complaints", value=0, subtitle="No data"),
                DashboardKpi(title="Open Cases", value=0, subtitle="Pending resolution"),
                DashboardKpi(title="Resolution Rate", value="0%", subtitle="Across processed reports"),
                DashboardKpi(title="Feedback Score", value="N/A", subtitle="Average rating"),
            ],
            charts=DashboardCharts(
                complaintTrends=ChartSection(title="Complaint Trends", items=[]),
                complaintCategories=ChartSection(title="Complaint Categories", items=[]),
                topZones=ChartSection(title="Top Zones", items=[]),
                topDivisions=ChartSection(title="Top Divisions", items=[]),
                topTrains=ChartSection(title="Top Trains", items=[]),
            ),
            analytics=DashboardAnalytics(
                feedback=[],
                resolution=[],
                observations=["No processed report data available."],
            ),
            recentActivity=[],
            sourceReports=source_reports,
            rowCount=0,
        )

    def _aggregate_field(
        self,
        rows: list[dict[str, Any]],
        mapper: ColumnMapper,
        field: str,
        limit: int,
    ) -> list[ChartDataPoint]:
        totals: Counter[str] = Counter()
        complaints_column = mapper.resolve("complaints")

        for row in rows:
            label = str(mapper.value(row, field, "Unknown") or "Unknown")
            weight = self._row_weight(row, complaints_column)
            totals[label] += weight

        items = [(label, count) for label, count in totals.most_common(limit)]
        return self._to_chart_items(items, limit=limit)

    def _group_by_weekday(
        self,
        rows: list[dict[str, Any]],
        mapper: ColumnMapper,
        limit: int,
    ) -> list[ChartDataPoint]:
        weekday_counts: Counter[str] = Counter()
        weekday_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        complaints_column = mapper.resolve("complaints")

        for row in rows:
            raw_date = mapper.value(row, "registration_date")
            parsed = self._parse_date(raw_date)
            if not parsed:
                continue
            label = parsed.strftime("%a")
            weekday_counts[label] += self._row_weight(row, complaints_column)

        if not weekday_counts:
            return []

        ordered = [
            (day, float(weekday_counts.get(day, 0)))
            for day in weekday_order
            if weekday_counts.get(day, 0) > 0
        ][:limit]
        return self._to_chart_items(ordered, limit=limit)

    def _feedback_breakdown(self, rows: list[dict[str, Any]], mapper: ColumnMapper) -> list[FeedbackMetric]:
        feedback_column = mapper.resolve("feedback")
        if not feedback_column:
            return []

        positive = negative = neutral = 0
        numeric_scores: list[float] = []

        for row in rows:
            raw = str(row.get(feedback_column, "")).strip()
            if not raw:
                continue

            lowered = raw.lower()
            if lowered in self.POSITIVE_FEEDBACK:
                positive += 1
            elif lowered in self.NEGATIVE_FEEDBACK:
                negative += 1
            else:
                try:
                    score = float(raw)
                    numeric_scores.append(score)
                    if score >= 4:
                        positive += 1
                    elif score <= 2:
                        negative += 1
                    else:
                        neutral += 1
                except ValueError:
                    neutral += 1

        total = positive + negative + neutral
        if total == 0:
            return []

        return [
            FeedbackMetric(label="Positive", value=f"{round((positive / total) * 100)}%", color="text-emerald-600"),
            FeedbackMetric(label="Negative", value=f"{round((negative / total) * 100)}%", color="text-red-600"),
            FeedbackMetric(label="Neutral", value=f"{round((neutral / total) * 100)}%", color="text-slate-600"),
            FeedbackMetric(label="Responses", value=str(total), color="text-slate-900"),
        ]

    def _resolution_rows(
        self,
        rows: list[dict[str, Any]],
        mapper: ColumnMapper,
        stats,
    ) -> list[AnalyticsRow]:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        resolved_today = 0
        escalated = 0
        closed_this_week = 0
        resolution_days: list[float] = []

        status_column = mapper.resolve("status")
        closed_column = mapper.resolve("closed_date")
        registration_column = mapper.resolve("registration_date")
        escalation_column = mapper.resolve("escalation")

        for row in rows:
            status = str(row.get(status_column, "")).lower().strip() if status_column else ""
            closed_raw = row.get(closed_column) if closed_column else None
            closed_date = self._parse_date(closed_raw)
            registered_date = self._parse_date(row.get(registration_column)) if registration_column else None

            if status in self.RESOLVED_STATUSES and closed_date == today:
                resolved_today += 1
            if closed_date and closed_date >= week_start and status in self.RESOLVED_STATUSES:
                closed_this_week += 1
            if escalation_column:
                try:
                    if int(float(row.get(escalation_column, 0) or 0)) > 0:
                        escalated += 1
                except (TypeError, ValueError):
                    pass
            if registered_date and closed_date and status in self.RESOLVED_STATUSES:
                delta = (closed_date - registered_date).days
                if delta >= 0:
                    resolution_days.append(float(delta))

        avg_days = round(mean(resolution_days), 1) if resolution_days else 0.0

        return [
            AnalyticsRow(label="Avg. resolution time", value=f"{avg_days} days"),
            AnalyticsRow(label="Resolved today", value=str(resolved_today or stats.resolved_complaints)),
            AnalyticsRow(label="Escalated", value=str(escalated)),
            AnalyticsRow(label="Closed this week", value=str(closed_this_week or stats.resolved_complaints)),
        ]

    def _count_by_date(self, rows: list[dict[str, Any]], mapper: ColumnMapper, target: date) -> int:
        count = 0
        for row in rows:
            parsed = self._parse_date(mapper.value(row, "registration_date"))
            if parsed == target:
                count += 1
        return count

    def _average_feedback_score(self, rows: list[dict[str, Any]], mapper: ColumnMapper) -> str:
        feedback_column = mapper.resolve("feedback")
        if not feedback_column:
            return "N/A"

        scores: list[float] = []
        for row in rows:
            raw = str(row.get(feedback_column, "")).strip()
            if not raw:
                continue
            try:
                scores.append(float(raw))
            except ValueError:
                lowered = raw.lower()
                if lowered in self.POSITIVE_FEEDBACK:
                    scores.append(4.5)
                elif lowered in self.NEGATIVE_FEEDBACK:
                    scores.append(2.0)
                else:
                    scores.append(3.0)

        if not scores:
            return "N/A"
        return f"{round(mean(scores), 1)} / 5"

    @staticmethod
    def _row_weight(row: dict[str, Any], complaints_column: str | None) -> float:
        if not complaints_column:
            return 1.0
        try:
            return float(row.get(complaints_column, 1) or 1)
        except (TypeError, ValueError):
            return 1.0

    @staticmethod
    def _to_chart_items(items: list[tuple[str, float | int]], limit: int) -> list[ChartDataPoint]:
        trimmed = items[:limit]
        if not trimmed:
            return []

        max_value = max(float(value) for _, value in trimmed) or 1.0
        return [
            ChartDataPoint(
                label=label,
                value=float(value),
                barWidth=round(min(100.0, (float(value) / max_value) * 100), 1),
            )
            for label, value in trimmed
        ]

    @staticmethod
    def _format_trend(today: int, yesterday: int) -> str:
        if yesterday == 0:
            return "+100% vs yesterday" if today > 0 else "No change vs yesterday"
        change = ((today - yesterday) / yesterday) * 100
        sign = "+" if change >= 0 else ""
        return f"{sign}{round(change)}% vs yesterday"

    @staticmethod
    def _parse_date(raw: Any) -> date | None:
        if raw is None or raw == "":
            return None
        if isinstance(raw, datetime):
            return raw.date()
        if isinstance(raw, date):
            return raw

        text = str(raw).strip()
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(text[:10], fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _relative_time(processed_at: str | None) -> str:
        if not processed_at:
            return "Just now"
        try:
            parsed = datetime.fromisoformat(processed_at.replace("Z", "+00:00"))
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
            return processed_at
