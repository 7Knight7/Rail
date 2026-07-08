"""Tests for UI configuration integration with processing engine."""

import pytest

from app.features.processing.engine import ReportProcessingEngine
from app.features.processing.schemas import (
    FilterConditionConfig,
    HighlightConfig,
    ReportConfiguration,
    SortingConfig,
    TopNConfig,
)
from app.features.rules.engine.context import Dataset


SAMPLE_ROWS = [
    {"Division": "Hyderabad", "Zone": "SCR", "Complaints": 120, "Current Status": "Open"},
    {"Division": "Secunderabad", "Zone": "SCR", "Complaints": 180, "Current Status": "Closed"},
    {"Division": "Vijayawada", "Zone": "ECoR", "Complaints": 95, "Current Status": "Open"},
    {"Division": "Warangal", "Zone": "SCR", "Complaints": 60, "Current Status": "Closed"},
]


@pytest.fixture
def sample_dataset():
    return Dataset(
        columns=["Division", "Zone", "Complaints", "Current Status"],
        rows=SAMPLE_ROWS,
        name="original",
    )


@pytest.mark.asyncio
async def test_configuration_filters_are_applied(sample_dataset):
    config = ReportConfiguration(
        filters=[FilterConditionConfig(column="Zone", operator="equals", value="SCR", logic="AND")],
        sorting=[SortingConfig(column="Complaints", direction="desc", priority=1)],
    )

    result = await ReportProcessingEngine().process(sample_dataset, config)

    assert result.row_count == 3
    assert all(row["Zone"] == "SCR" for row in result.dataset.rows)
    assert "filter" in result.steps_applied


@pytest.mark.asyncio
async def test_configuration_visible_columns_and_top_n(sample_dataset):
    config = ReportConfiguration(
        sorting=[SortingConfig(column="Complaints", direction="desc", priority=1)],
        topN=TopNConfig(enabled=True, mode="top", count=2, byColumn="Complaints"),
        hiddenColumns=["Current Status"],
        columnOrder=["Complaints", "Division", "Zone"],
    )

    result = await ReportProcessingEngine().process(sample_dataset, config)

    assert result.row_count == 2
    assert result.dataset.columns == ["Complaints", "Division", "Zone"]
    assert "top_n" in result.steps_applied


@pytest.mark.asyncio
async def test_configuration_contains_filter_operator(sample_dataset):
    config = ReportConfiguration(
        filters=[FilterConditionConfig(column="Division", operator="contains", value="Secunder", logic="AND")],
    )

    result = await ReportProcessingEngine().process(sample_dataset, config)

    assert result.row_count == 1
    assert result.dataset.rows[0]["Division"] == "Secunderabad"


@pytest.mark.asyncio
async def test_configuration_highlight_rules(sample_dataset):
    config = ReportConfiguration(
        highlights=[
            HighlightConfig(
                column="Complaints",
                scope="row",
                operator="gt",
                value=100,
                backgroundColor="#FFF4CC",
            )
        ],
    )

    result = await ReportProcessingEngine().process(sample_dataset, config)

    assert len(result.highlights) > 0
    assert result.highlights[0].background_color == "#FFF4CC"
