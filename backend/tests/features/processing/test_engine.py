import pytest
from openpyxl import Workbook

from app.core.spreadsheet.excel_reader import ExcelReader
from app.features.processing.converters import dataset_from_excel
from app.features.processing.engine import ReportProcessingEngine
from app.features.processing.rules.schemas import ReportRulesConfig
from app.features.processing.schemas import (
    FilterConditionConfig,
    GroupAggregationConfig,
    GroupingConfig,
    HighlightConfig,
    ReportConfiguration,
    SortingConfig,
    TopNConfig,
)


@pytest.fixture
def sample_dataset(tmp_path):
    path = tmp_path / "division_report.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Division", "Zone", "Complaints", "Status"])
    sheet.append(["Hyderabad", "SCR", 120, "Open"])
    sheet.append(["Secunderabad", "SCR", 180, "Closed"])
    sheet.append(["Vijayawada", "SCR", 95, "Open"])
    sheet.append(["Warangal", "SCR", 60, "Closed"])
    workbook.save(path)
    workbook.close()
    return dataset_from_excel(ExcelReader().read(path))


@pytest.mark.asyncio
async def test_process_applies_filter_and_sort(sample_dataset):
    config = ReportConfiguration(
        filters=[
            FilterConditionConfig(column="Zone", operator="equals", value="SCR", logic="AND"),
            FilterConditionConfig(column="Status", operator="equals", value="Open", logic="AND"),
        ],
        sorting=[SortingConfig(column="Complaints", direction="desc", priority=1)],
    )

    result = await ReportProcessingEngine().process(sample_dataset, config)

    assert result.row_count == 2
    assert result.dataset.rows[0]["Division"] == "Hyderabad"
    assert "filter" in result.steps_applied
    assert "sort" in result.steps_applied


@pytest.mark.asyncio
async def test_process_applies_top_n(sample_dataset):
    config = ReportConfiguration(
        sorting=[SortingConfig(column="Complaints", direction="desc", priority=1)],
        topN=TopNConfig(enabled=True, mode="top", count=2, byColumn="Complaints"),
    )

    result = await ReportProcessingEngine().process(sample_dataset, config)

    assert result.row_count == 2
    assert result.dataset.rows[0]["Division"] == "Secunderabad"
    assert result.dataset.rows[1]["Division"] == "Hyderabad"


@pytest.mark.asyncio
async def test_process_applies_grouping(sample_dataset):
    config = ReportConfiguration(
        grouping=GroupingConfig(
            enabled=True,
            groupBy=["Zone"],
            aggregations=[
                GroupAggregationConfig(column="Complaints", function="sum", outputColumn="Total Complaints")
            ],
        )
    )

    result = await ReportProcessingEngine().process(sample_dataset, config)

    assert result.row_count == 1
    assert result.dataset.rows[0]["Total Complaints"] == 455


@pytest.mark.asyncio
async def test_process_hides_and_reorders_columns(sample_dataset):
    config = ReportConfiguration(
        hiddenColumns=["Status"],
        columnOrder=["Complaints", "Division", "Zone"],
    )

    result = await ReportProcessingEngine().process(sample_dataset, config)

    assert result.dataset.columns == ["Complaints", "Division", "Zone"]
    assert "Status" not in result.dataset.rows[0]


@pytest.mark.asyncio
async def test_process_applies_row_highlights(sample_dataset):
    config = ReportConfiguration(
        highlights=[
            HighlightConfig(
                column="Complaints",
                scope="row",
                operator="gt",
                value=100,
                backgroundColor="#FFF4CC",
            )
        ]
    )

    result = await ReportProcessingEngine().process(sample_dataset, config)

    assert len(result.highlights) > 0
    assert result.highlights[0].background_color == "#FFF4CC"


@pytest.mark.asyncio
async def test_same_engine_works_for_different_configs(sample_dataset):
    division_config = ReportConfiguration(
        sorting=[SortingConfig(column="Complaints", direction="desc", priority=1)],
        topN=TopNConfig(enabled=True, mode="bottom", count=1, byColumn="Complaints"),
    )
    zone_config = ReportConfiguration(
        grouping=GroupingConfig(
            enabled=True,
            groupBy=["Zone"],
            aggregations=[GroupAggregationConfig(column="Division", function="count", outputColumn="Divisions")],
        )
    )

    division_result = await ReportProcessingEngine().process(sample_dataset, division_config)
    zone_result = await ReportProcessingEngine().process(sample_dataset, zone_config)

    assert division_result.row_count == 1
    assert zone_result.row_count == 1
    assert division_result.dataset.columns != zone_result.dataset.columns
