"""Report definitions and metadata for automation runs."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportDefinition:
    """Describes a single downloadable report."""

    name: str
    slug: str


class ReportCatalog:
    """Registry of reports to download during an automation run."""

    def __init__(self, reports: list[ReportDefinition] | None = None) -> None:
        self._reports = list(reports or [])

    @property
    def reports(self) -> list[ReportDefinition]:
        return list(self._reports)

    def add(self, report: ReportDefinition) -> None:
        self._reports.append(report)
