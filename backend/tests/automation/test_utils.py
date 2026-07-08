"""Unit tests for automation logging utilities."""

import logging

from app.automation.utils import log_automation_event


def test_log_automation_event_sanitizes_reserved_keys(caplog):
    caplog.set_level(logging.INFO)
    test_logger = logging.getLogger("test.automation.logging")

    log_automation_event(
        test_logger,
        "filter_field_discovered",
        name="fromDate",
        type="text",
        label="From Date",
        value="08/07/2026",
        id="fromDate",
    )

    assert "filter_field_discovered" in caplog.text
    assert "field_name=fromDate" in caplog.text
    assert "field_type=text" in caplog.text
    assert "field_label=From Date" in caplog.text
    assert "field_value=08/07/2026" in caplog.text
    assert "field_id=fromDate" in caplog.text
