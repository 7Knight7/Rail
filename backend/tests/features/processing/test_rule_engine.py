import pytest
from openpyxl import Workbook

from app.core.spreadsheet.excel_reader import ExcelReader
from app.features.processing.converters import dataset_from_excel
from app.features.processing.engine import ReportProcessingEngine
from app.features.processing.rules.compiler import RuleCompiler
from app.features.processing.rules.registry import get_report_rules
from app.features.processing.rules.schemas import ReportRulesConfig


@pytest.fixture
def zone_dataset(tmp_path):
    path = tmp_path / "zone_report.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Zone", "Division", "Registration Date", "Complaints", "Status"])
    sheet.append(["South Central Railway", "Hyderabad", "2026-07-01", 120, "Open"])
    sheet.append(["South Central Railway", "Secunderabad", "2026-07-02", 180, "Closed"])
    sheet.append(["Northern Railway", "Delhi", "2026-07-03", 95, "Open"])
    workbook.save(path)
    workbook.close()
    return dataset_from_excel(ExcelReader().read(path))


@pytest.fixture
def division_dataset(tmp_path):
    path = tmp_path / "division_report.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Division", "Zone", "Registration Date", "Complaints"])
    for index in range(30):
        sheet.append([f"Division-{index + 1}", "SCR", f"2026-07-{index + 1:02d}", 100 - index])
    workbook.save(path)
    workbook.close()
    return dataset_from_excel(ExcelReader().read(path))


@pytest.mark.asyncio
async def test_zone_report_rules_from_registry(zone_dataset):
    config = get_report_rules("merging").rules
    config.sort_by = "Complaints"
    config.order = "DESC"

    result = await ReportProcessingEngine().process_report_config(zone_dataset, config)

    assert "sort" in result.steps_applied
    assert "hide_columns" in result.steps_applied
    assert "highlight_rows" in result.steps_applied
    assert "Registration Date" not in result.dataset.columns


@pytest.mark.asyncio
async def test_division_report_top_n_from_registry(division_dataset):
    config = get_report_rules("division").rules
    config.sort_by = "Complaints"

    result = await ReportProcessingEngine().process_report_config(division_dataset, config)

    assert result.row_count == 25
    assert result.dataset.rows[0]["Complaints"] == 71


@pytest.mark.asyncio
async def test_train_report_top_n_config(division_dataset):
    config = ReportRulesConfig(topN=20, sortBy="Complaints", order="DESC")

    result = await ReportProcessingEngine().process_report_config(division_dataset, config)

    assert result.row_count == 20


def test_rule_compiler_has_no_report_specific_branching():
    columns = ["Zone", "Division", "Complaints"]
    zone_rules = RuleCompiler().compile(
        ReportRulesConfig(
            sortBy="Complaints",
            order="DESC",
            hideColumns=["Status"],
            highlightRows="Zone == SCR",
        ),
        columns,
    )
    division_rules = RuleCompiler().compile(
        ReportRulesConfig(topN=25, sortBy="Complaints", order="DESC"),
        columns,
    )

    assert {rule.type for rule in zone_rules} == {"sort", "hide_columns", "highlight_rows"}
    assert {rule.type for rule in division_rules} == {"sort", "top_n"}
