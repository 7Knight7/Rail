"""Tests for DashboardAggregator."""

from datetime import date

from app.features.dashboard.aggregator import DashboardAggregator
from app.features.dashboard.schemas import ProcessedReportInput
from app.features.processing.schemas import ProcessDatasetResponse, ProcessedColumn


def _processed_report(rows: list[dict], report_id: str = "merging") -> ProcessedReportInput:
    columns = list(rows[0].keys()) if rows else []
    return ProcessedReportInput(
        reportId=report_id,
        reportName="Zone Wise Report",
        processedAt="2026-07-08T10:00:00+00:00",
        data=ProcessDatasetResponse(
            columns=[ProcessedColumn(name=column, index=index) for index, column in enumerate(columns)],
            rows=rows,
            highlights=[],
            rowCount=len(rows),
            columnCount=len(columns),
            stepsApplied=["filter", "sort"],
            warnings=[],
        ),
    )


SAMPLE_ROWS = [
    {
        "Grievance ID": "GRV-1",
        "Zone": "SCR",
        "Division": "Hyderabad",
        "Train No": "12713",
        "Category": "Cleanliness",
        "Registration Date": date.today().isoformat(),
        "Closed Date": date.today().isoformat(),
        "Current Status": "Resolved",
        "Feedback": "4",
        "Complaints": 1,
        "Escalation Level": 0,
    },
    {
        "Grievance ID": "GRV-2",
        "Zone": "SCR",
        "Division": "Secunderabad",
        "Train No": "12724",
        "Category": "Punctuality",
        "Registration Date": date.today().isoformat(),
        "Closed Date": "",
        "Current Status": "Open",
        "Feedback": "2",
        "Complaints": 1,
        "Escalation Level": 1,
    },
    {
        "Grievance ID": "GRV-3",
        "Zone": "SCR",
        "Division": "Vijayawada",
        "Train No": "17229",
        "Category": "Cleanliness",
        "Registration Date": "2026-07-01",
        "Closed Date": "2026-07-03",
        "Current Status": "Closed",
        "Feedback": "Positive",
        "Complaints": 1,
        "Escalation Level": 0,
    },
]


class TestDashboardAggregator:
    def setup_method(self):
        self.aggregator = DashboardAggregator()

    def test_builds_kpis_from_processed_reports(self):
        dashboard = self.aggregator.build([_processed_report(SAMPLE_ROWS)])

        assert len(dashboard.kpis) == 4
        assert dashboard.kpis[0].title == "Today's Complaints"
        assert dashboard.kpis[1].value >= 1
        assert "%" in str(dashboard.kpis[2].value)

    def test_builds_charts_with_backend_bar_width(self):
        dashboard = self.aggregator.build([_processed_report(SAMPLE_ROWS)])

        assert dashboard.charts.top_zones.items
        assert all(0 <= item.bar_width <= 100 for item in dashboard.charts.top_zones.items)
        assert dashboard.charts.complaint_categories.items
        assert dashboard.charts.top_trains.items

    def test_builds_analytics_and_recent_activity(self):
        dashboard = self.aggregator.build([_processed_report(SAMPLE_ROWS)])

        assert dashboard.analytics.feedback
        assert dashboard.analytics.resolution
        assert dashboard.analytics.observations
        assert dashboard.recent_activity
        assert dashboard.row_count == 3

    def test_empty_reports_return_safe_defaults(self):
        dashboard = self.aggregator.build([])

        assert dashboard.row_count == 0
        assert dashboard.kpis[0].value == 0
        assert dashboard.analytics.observations == ["No processed report data available."]

    def test_deduplicates_rows_by_grievance_id(self):
        duplicate_rows = SAMPLE_ROWS + [SAMPLE_ROWS[0]]
        dashboard = self.aggregator.build([_processed_report(duplicate_rows)])

        assert dashboard.row_count == 3
