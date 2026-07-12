"""Filter definitions for MIS Report 2 (Division Wise Top 25)."""

from __future__ import annotations

from app.automation.report1_filters import FilterFieldDefinition, _label_select


REPORT_2_FILTERS: list[FilterFieldDefinition] = [
    FilterFieldDefinition(
        name="dateRange",
        selector=(
            "select[name*='dateRange'], select[id*='dateRange'], "
            "select[name*='DateRange'], select[id*='DateRange']"
        ),
        field_type="select",
        value="Previous Day",
        required=True,
        label="Date Range",
    ),
    _label_select("Excluding Refund Cases", "YES"),
    _label_select("Excluding Inquiry Cases", "YES"),
    _label_select("Zone", "ALL"),
    _label_select("Division", "ALL"),
    _label_select("Department", "ALL"),
    _label_select("Mode", "ALL"),
    _label_select("Type", "ALL"),
    _label_select("Sub Type", "ALL"),
    _label_select("View", "Division Wise"),
    _label_select("Excluding Assistance Cases", "Yes"),
    _label_select("Channel Type", "ALL", required=False),
    _label_select("Train Type", "ALL", required=False),
]


REPORT_2_FEEDBACK_FILTERS: list[FilterFieldDefinition] = [
    FilterFieldDefinition(
        name="dateRange",
        selector=(
            "select[name*='dateRange'], select[id*='dateRange'], "
            "select[name*='DateRange'], select[id*='DateRange']"
        ),
        field_type="select",
        value="Previous Day",
        required=True,
        label="Date Range",
    ),
    _label_select("Excluding Refund Cases", "YES"),
    _label_select("Excluding Inquiry Cases", "YES"),
    _label_select("Zone", "ALL"),
    _label_select("Division", "ALL"),
    _label_select("Department", "ALL"),
    _label_select("Mode", "ALL"),
    _label_select("Type", "ALL"),
    _label_select("Sub Type", "ALL"),
    _label_select("View", "Division Wise"),
    _label_select("Excluding Assistance Cases", "Yes"),
]


def filters_for_report2() -> list[FilterFieldDefinition]:
    """Return the curated filter list for Report 2 Comprehensive Division Wise."""
    return list(REPORT_2_FILTERS)


def filters_for_report2_feedback() -> list[FilterFieldDefinition]:
    """Return the curated filter list for Report 2 Feedback Division Wise."""
    return list(REPORT_2_FEEDBACK_FILTERS)
