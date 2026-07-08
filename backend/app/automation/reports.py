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


class ReportCatalog:
    """Registry of reports to navigate during an automation run."""

    def __init__(self, reports: list[ReportDefinition] | None = None) -> None:
        self._reports = list(reports or [REPORT_1])

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


catalog = ReportCatalog()
