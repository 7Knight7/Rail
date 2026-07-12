"""Report definitions and metadata for automation runs."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportDefinition:
    """Describes a single portal report page for navigation."""

    name: str
    slug: str
    page_path: str
    screenshot_filename: str
    url_fragment: str


REPORT_1 = ReportDefinition(
    name="MIS Report 1",
    slug="report1",
    page_path="/mis_reports/report1",
    screenshot_filename="report1.png",
    url_fragment="mis_reports/report1",
)

REPORT_2 = ReportDefinition(
    name="Comprehensive (with drill down) - Division Wise",
    slug="division",
    page_path="/mis_reports/report1",
    screenshot_filename="division.png",
    url_fragment="mis_reports/report1",
)

REPORT_6_FEEDBACK = ReportDefinition(
    name="Feedback (with drill down)",
    slug="report6",
    page_path="/mis_reports/report6",
    screenshot_filename="report6.png",
    url_fragment="mis_reports/report6",
)

REPORT_10_ZONE_TRAIN_TYPE = ReportDefinition(
    name="Zone/Train Type wise Report",
    slug="report10",
    page_path="/mis_reports/report16",
    screenshot_filename="report10.png",
    url_fragment="mis_reports/report16",
)

REPORT_3_TRAIN_NO = ReportDefinition(
    name="Zone/Train Type wise Report - Train No. Wise",
    slug="train-no",
    page_path="/mis_reports/report16",
    screenshot_filename="train-no.png",
    url_fragment="mis_reports/report16",
)

REPORT_4_TYPES = ReportDefinition(
    name="Zone/Train Type wise Report - Type Wise",
    slug="types",
    page_path="/mis_reports/report16",
    screenshot_filename="types.png",
    url_fragment="mis_reports/report16",
)

REPORT_5_SCR_TRAIN = ReportDefinition(
    name="Feedback - SCR Train Unsatisfactory",
    slug="scr-train",
    page_path="/mis_reports/report6",
    screenshot_filename="scr-train.png",
    url_fragment="mis_reports/report6",
)

REPORT_6_SCR_STATION = ReportDefinition(
    name="Feedback - SCR Station Unsatisfactory",
    slug="scr-station",
    page_path="/mis_reports/report6",
    screenshot_filename="scr-station.png",
    url_fragment="mis_reports/report6",
)

DEFAULT_CATALOG = [
    REPORT_1,
    REPORT_2,
    REPORT_3_TRAIN_NO,
    REPORT_4_TYPES,
    REPORT_5_SCR_TRAIN,
    REPORT_6_SCR_STATION,
]


class ReportCatalog:
    """Registry of reports to navigate during an automation run."""

    def __init__(self, reports: list[ReportDefinition] | None = None) -> None:
        self._reports = list(reports or DEFAULT_CATALOG)

    @property
    def reports(self) -> list[ReportDefinition]:
        return list(self._reports)

    def first_report(self) -> ReportDefinition:
        """Return the first report in the navigation sequence."""
        if not self._reports:
            raise ValueError("Report catalog is empty")
        return self._reports[0]

    def add(self, report: ReportDefinition) -> None:
        self._reports.append(report)


catalog = ReportCatalog(DEFAULT_CATALOG)
