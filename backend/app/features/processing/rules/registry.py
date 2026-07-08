"""Default per-report rule configuration registry."""

from __future__ import annotations

from app.features.processing.rules.schemas import ReportRuleSet, ReportRulesConfig

REPORT_RULE_REGISTRY: dict[str, ReportRuleSet] = {
    "merging": ReportRuleSet(
        reportId="merging",
        reportName="Zone Wise Report",
        rules=ReportRulesConfig(
            sortBy="Received",
            order="DESC",
            hideColumns=["C", "G", "J", "K"],
            highlightRows="Zone == South Central Railway",
        ),
    ),
    "division": ReportRuleSet(
        reportId="division",
        reportName="Division (Bottom 25)",
        rules=ReportRulesConfig(
            topN=25,
            sortBy="Received",
            order="ASC",
            topNMode="bottom",
        ),
    ),
    "train-no": ReportRuleSet(
        reportId="train-no",
        reportName="Top 20 Trains",
        rules=ReportRulesConfig(
            topN=20,
            sortBy="Received",
            order="DESC",
        ),
    ),
    "types": ReportRuleSet(
        reportId="types",
        reportName="Cause Wise Analysis",
        rules=ReportRulesConfig(
            topN=10,
            sortBy="Complaints",
            order="DESC",
        ),
    ),
    "scr-train": ReportRuleSet(
        reportId="scr-train",
        reportName="SCR Train Report",
        rules=ReportRulesConfig(
            sortBy="Complaints",
            order="DESC",
            filters=["Zone == SCR"],
        ),
    ),
    "scr-station": ReportRuleSet(
        reportId="scr-station",
        reportName="SCR Station Report",
        rules=ReportRulesConfig(
            sortBy="Complaints",
            order="DESC",
            filters=["Zone == SCR"],
        ),
    ),
}


def get_report_rules(report_id: str) -> ReportRuleSet | None:
    return REPORT_RULE_REGISTRY.get(report_id)


def list_report_rules() -> list[ReportRuleSet]:
    return list(REPORT_RULE_REGISTRY.values())
