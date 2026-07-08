"""Tests for output generation from processed datasets."""

import json
from pathlib import Path

import pytest

from app.features.outputs.dashboard_json_exporter import DashboardJsonExporter
from app.features.outputs.excel_exporter import ExcelExporter
from app.features.outputs.pdf_exporter import PdfExporter
from app.features.outputs.service import OutputGenerationService
from app.features.outputs.schemas import GenerateOutputsRequest
from app.features.processing.schemas import ProcessDatasetResponse, ProcessedColumn


def _processed_dataset() -> ProcessDatasetResponse:
    return ProcessDatasetResponse(
        columns=[
            ProcessedColumn(name="Division", index=0),
            ProcessedColumn(name="Zone", index=1),
            ProcessedColumn(name="Complaints", index=2),
            ProcessedColumn(name="Status", index=3),
        ],
        rows=[
            {"Division": "Hyderabad", "Zone": "SCR", "Complaints": 120, "Status": "Open"},
            {"Division": "Secunderabad", "Zone": "SCR", "Complaints": 180, "Status": "Closed"},
        ],
        highlights=[
            {
                "rowIndex": 0,
                "column": None,
                "backgroundColor": "#FFF4CC",
                "textColor": None,
                "bold": False,
            }
        ],
        rowCount=2,
        columnCount=4,
        stepsApplied=["sort", "filter"],
        warnings=[],
    )


class TestOutputExporters:
    def test_excel_exporter_writes_workbook(self, tmp_path: Path):
        output_path = tmp_path / "report.xlsx"
        ExcelExporter().write(_processed_dataset(), output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_pdf_exporter_writes_document(self, tmp_path: Path):
        output_path = tmp_path / "report.pdf"
        PdfExporter().write(_processed_dataset(), "Division Report", output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_dashboard_json_exporter_writes_file(self, tmp_path: Path):
        from app.features.dashboard.aggregator import DashboardAggregator
        from app.features.dashboard.schemas import ProcessedReportInput

        dashboard = DashboardAggregator().build(
            [
                ProcessedReportInput(
                    reportId="division",
                    reportName="Division Report",
                    processedAt="2026-07-08T10:00:00+00:00",
                    data=_processed_dataset(),
                )
            ]
        )
        output_path = tmp_path / "dashboard.json"
        DashboardJsonExporter().write(dashboard, output_path)

        assert output_path.exists()
        assert "kpis" in output_path.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_output_service_generates_all_artifacts(tmp_path: Path):
    service = OutputGenerationService(session=None)  # type: ignore[arg-type]
    service._exports_dir = tmp_path

    response = await service.generate(
        GenerateOutputsRequest(
            reportId="division",
            reportName="Division Report",
            processed=_processed_dataset(),
        )
    )

    assert response.report_id == "division"
    assert response.processed.row_count == 2
    assert response.dashboard is not None
    assert len(response.artifacts) == 3
    assert {artifact.format for artifact in response.artifacts} == {"excel", "pdf", "dashboard_json"}

    manifest_path = tmp_path / response.batch_id / "manifest.json"
    assert manifest_path.exists()

    for artifact in response.artifacts:
        assert Path(artifact.path).exists()


def test_list_generated_reports_from_manifest(tmp_path: Path):
    service = OutputGenerationService(session=None)  # type: ignore[arg-type]
    service._exports_dir = tmp_path

    batch_dir = tmp_path / "batch-123"
    batch_dir.mkdir()
    (batch_dir / "division_report_20260708_division.xlsx").write_bytes(b"xlsx")
    (batch_dir / "division_report_20260708_division.pdf").write_bytes(b"pdf")
    (batch_dir / "manifest.json").write_text(
        json.dumps(
            {
                "batchId": "batch-123",
                "reportId": "division",
                "reportName": "Division Report",
                "reportType": "Division Report",
                "generatedAt": "2026-07-08T10:00:00+00:00",
                "status": "completed",
                "artifacts": [
                    {
                        "format": "excel",
                        "filename": "division_report_20260708_division.xlsx",
                        "path": str(batch_dir / "division_report_20260708_division.xlsx"),
                        "downloadUrl": "/api/v1/outputs/batch-123/download?format=excel",
                        "size": 4,
                    },
                    {
                        "format": "pdf",
                        "filename": "division_report_20260708_division.pdf",
                        "path": str(batch_dir / "division_report_20260708_division.pdf"),
                        "downloadUrl": "/api/v1/outputs/batch-123/download?format=pdf",
                        "size": 3,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    result = service.list_reports()

    assert result.total == 1
    assert result.reports[0].report_name == "Division Report"
    assert result.reports[0].excel_download_url is not None
    assert result.reports[0].pdf_download_url is not None


def test_list_generated_reports_supports_search_and_sort(tmp_path: Path):
    service = OutputGenerationService(session=None)  # type: ignore[arg-type]
    service._exports_dir = tmp_path

    for index, report in enumerate(
        [
            ("batch-a", "Division Report", "division", "2026-07-08T09:00:00+00:00"),
            ("batch-b", "Train Report", "train-no", "2026-07-08T11:00:00+00:00"),
        ]
    ):
        batch_dir = tmp_path / report[0]
        batch_dir.mkdir()
        (batch_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "batchId": report[0],
                    "reportId": report[2],
                    "reportName": report[1],
                    "reportType": report[1],
                    "generatedAt": report[3],
                    "status": "completed",
                    "artifacts": [],
                }
            ),
            encoding="utf-8",
        )

    searched = service.list_reports(search="train")
    assert searched.total == 1
    assert searched.reports[0].report_id == "train-no"

    sorted_reports = service.list_reports(sort_by="generatedAt", sort_order="asc")
    assert sorted_reports.reports[0].batch_id == "batch-a"
    assert sorted_reports.reports[1].batch_id == "batch-b"
