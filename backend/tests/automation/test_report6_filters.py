"""Tests for Report 6 Feedback filter definitions."""

from app.automation.report1_filters import (
    REPORT_1_FILTERS,
    REPORT_6_FILTERS,
    build_filters_from_discovery,
    filters_for_report,
    resolve_filter_value,
)


def test_report1_date_range_is_previous_day():
    values_by_label = {f.label: f.value for f in REPORT_1_FILTERS}
    assert values_by_label["Date Range"] == "Previous Day"
    assert resolve_filter_value(REPORT_1_FILTERS[0].value) == "Previous Day"


def test_report1_discovery_date_range_is_previous_day():
    filters = build_filters_from_discovery(
        [
            {
                "tag": "select",
                "field_id": "dateRange",
                "field_name": "dateRange",
                "field_type": "select-one",
                "field_label": "Date Range",
                "selector": "#dateRange",
                "current_value": "Current Day",
                "required": False,
                "options": [],
            }
        ],
        slug="report1",
    )
    assert filters[0].value == "Previous Day"
    assert resolve_filter_value(filters[0].value) == "Previous Day"


def test_report6_filters_defined():
    values_by_label = {f.label: f.value for f in REPORT_6_FILTERS}
    assert values_by_label["Date Range"] == "Previous Day"
    assert values_by_label["View"] == "Zone Wise / Dept. Wise"
    assert values_by_label["Zone"] == "ALL"
    assert values_by_label["Division"] == "ALL"
    assert values_by_label["Department"] == "ALL"
    assert values_by_label["Mode"] == "ALL"
    assert values_by_label["Type"] == "ALL"
    assert values_by_label["Sub Type"] == "ALL"
    assert values_by_label["Excluding Refund Cases"] == "YES"
    assert values_by_label["Excluding Inquiry Cases"] == "YES"
    assert values_by_label["Excluding Assistance Cases"] == "Yes"


def test_build_filters_from_discovery_returns_report6_filters():
    filters = build_filters_from_discovery([], slug="report6")
    assert filters == list(REPORT_6_FILTERS)
    assert filters_for_report("report6") == list(REPORT_6_FILTERS)


def test_report1_feedback_dataset_id_supported():
    from app.features.datasets.service import SUPPORTED_REPORT_IDS

    assert "report1" in SUPPORTED_REPORT_IDS
    assert "report1_feedback" in SUPPORTED_REPORT_IDS
