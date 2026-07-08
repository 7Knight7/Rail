"""Unit tests for report catalog."""

from app.automation.reports import REPORT_1, ReportCatalog, catalog


def test_first_report_is_mis_report_1():
    report = catalog.first_report()
    assert report == REPORT_1
    assert report.name == "MIS Report 1"
    assert report.slug == "report1"
    assert report.page_path == "/mis_reports/report1"
    assert report.screenshot_filename == "report1.png"
    assert report.url_fragment == "mis_reports/report1"


def test_report_catalog_first_report():
    custom = ReportCatalog([REPORT_1])
    assert custom.first_report() is REPORT_1
