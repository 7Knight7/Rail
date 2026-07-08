"""Generate final Excel, PDF, and dashboard JSON from processed datasets."""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.features.dashboard.aggregator import DashboardAggregator
from app.features.dashboard.schemas import ProcessedReportInput
from app.features.outputs.csv_exporter import CsvExporter
from app.features.outputs.dashboard_json_exporter import DashboardJsonExporter
from app.features.outputs.excel_exporter import ExcelExporter
from app.features.outputs.manifest import read_manifest, write_manifest
from app.features.outputs.pdf_exporter import PdfExporter
from app.features.outputs.schemas import (
    GenerateOutputsRequest,
    GenerateOutputsResponse,
    GeneratedReportItem,
    GeneratedReportListResponse,
    OutputArtifact,
)
from app.features.processing.rules.registry import get_report_rules
from app.features.processing.schemas import ProcessDatasetRequest
from app.features.processing.service import ReportProcessingService

REPORT_TYPE_LABELS: dict[str, str] = {
    "merging": "Zone Report",
    "division": "Division Report",
    "train-no": "Train Report",
    "types": "Cause Analysis",
    "scr-train": "SCR Train Report",
    "scr-station": "SCR Station Report",
}


class OutputGenerationService:
    """Orchestrate final output generation from processed report data."""

    def __init__(self, session: AsyncSession) -> None:
        self._processing_service = ReportProcessingService(session)
        self._dashboard_aggregator = DashboardAggregator()
        self._excel_exporter = ExcelExporter()
        self._pdf_exporter = PdfExporter()
        self._csv_exporter = CsvExporter()
        self._dashboard_exporter = DashboardJsonExporter()
        self._exports_dir = Path(settings.exports_directory)

    async def generate(self, request: GenerateOutputsRequest) -> GenerateOutputsResponse:
        processed = request.processed
        if processed is None:
            processed = await self._processing_service.process(
                ProcessDatasetRequest(
                    reportId=request.report_id,
                    configuration=request.configuration,
                    rules=request.rules,
                )
            )

        report_name = request.report_name or self._resolve_report_name(request.report_id)
        batch_id = str(uuid.uuid4())
        batch_dir = self._exports_dir / batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)
        generated_at = datetime.now(UTC).isoformat()

        artifacts: list[OutputArtifact] = []
        dashboard = None

        if request.include_excel:
            excel_name = self._build_filename(report_name, request.report_id, "xlsx")
            excel_path = self._excel_exporter.write(processed, batch_dir / excel_name)
            artifacts.append(self._artifact(batch_id, "excel", excel_name, excel_path))

        if request.include_pdf:
            pdf_name = self._build_filename(report_name, request.report_id, "pdf")
            pdf_path = self._pdf_exporter.write(processed, report_name, batch_dir / pdf_name)
            artifacts.append(self._artifact(batch_id, "pdf", pdf_name, pdf_path))

        if request.include_csv:
            csv_name = self._build_filename(report_name, request.report_id, "csv")
            csv_path = self._csv_exporter.write(processed, batch_dir / csv_name)
            artifacts.append(self._artifact(batch_id, "csv", csv_name, csv_path))

        if request.include_dashboard:
            dashboard = self._dashboard_aggregator.build(
                [
                    ProcessedReportInput(
                        reportId=request.report_id,
                        reportName=report_name,
                        processedAt=generated_at,
                        data=processed,
                    )
                ],
                period=request.period,
            )
            json_name = self._build_filename(report_name, request.report_id, "json")
            json_path = self._dashboard_exporter.write(dashboard, batch_dir / json_name)
            artifacts.append(self._artifact(batch_id, "dashboard_json", json_name, json_path))

        write_manifest(
            batch_dir,
            {
                "batchId": batch_id,
                "reportId": request.report_id,
                "reportName": report_name,
                "reportType": self._report_type_label(request.report_id),
                "generatedAt": generated_at,
                "status": self._resolve_status(artifacts),
                "artifacts": [artifact.model_dump(by_alias=True) for artifact in artifacts],
            },
        )

        return GenerateOutputsResponse(
            batchId=batch_id,
            reportId=request.report_id,
            reportName=report_name,
            generatedAt=generated_at,
            processed=processed,
            dashboard=dashboard,
            artifacts=artifacts,
        )

    def resolve_download_path(self, batch_id: str, format: str) -> Path:
        batch_dir = self._exports_dir / batch_id
        if not batch_dir.exists():
            raise ValidationError("Output batch not found")

        extension_map = {
            "excel": ".xlsx",
            "pdf": ".pdf",
            "csv": ".csv",
            "dashboard": ".json",
            "dashboard_json": ".json",
        }
        extension = extension_map.get(format)
        if not extension:
            raise ValidationError("Unsupported output format")

        matches = list(batch_dir.glob(f"*{extension}"))
        if not matches:
            raise ValidationError(f"No {format} artifact found for this batch")
        return matches[0]

    def list_reports(
        self,
        search: str | None = None,
        sort_by: str = "generatedAt",
        sort_order: str = "desc",
    ) -> GeneratedReportListResponse:
        reports: list[GeneratedReportItem] = []

        if not self._exports_dir.exists():
            return GeneratedReportListResponse(reports=[], total=0)

        for batch_dir in self._exports_dir.iterdir():
            if not batch_dir.is_dir():
                continue

            item = self._load_report_item(batch_dir)
            if item is None:
                continue
            reports.append(item)

        if search:
            query = search.lower().strip()
            reports = [
                report
                for report in reports
                if query in report.report_name.lower()
                or query in report.report_type.lower()
                or query in report.report_id.lower()
                or query in report.status.lower()
            ]

        reverse = sort_order.lower() != "asc"
        sort_key = {
            "reportName": lambda item: item.report_name.lower(),
            "reportType": lambda item: item.report_type.lower(),
            "generatedAt": lambda item: item.generated_at,
            "status": lambda item: item.status,
        }.get(sort_by, lambda item: item.generated_at)
        reports.sort(key=sort_key, reverse=reverse)

        return GeneratedReportListResponse(reports=reports, total=len(reports))

    def _load_report_item(self, batch_dir: Path) -> GeneratedReportItem | None:
        manifest = read_manifest(batch_dir)
        if manifest:
            return self._item_from_manifest(manifest)

        artifacts = self._discover_artifacts(batch_dir.name, batch_dir)
        if not artifacts:
            return None

        report_id = self._infer_report_id(batch_dir)
        report_name = self._resolve_report_name(report_id)
        generated_at = datetime.fromtimestamp(batch_dir.stat().st_mtime, UTC).isoformat()

        return GeneratedReportItem(
            batchId=batch_dir.name,
            reportId=report_id,
            reportName=report_name,
            reportType=self._report_type_label(report_id),
            generatedAt=generated_at,
            status=self._resolve_status(artifacts),
            excelDownloadUrl=self._artifact_url(batch_dir.name, "excel", artifacts),
            pdfDownloadUrl=self._artifact_url(batch_dir.name, "pdf", artifacts),
            excelSize=self._artifact_size(artifacts, "excel"),
            pdfSize=self._artifact_size(artifacts, "pdf"),
        )

    def _item_from_manifest(self, manifest: dict) -> GeneratedReportItem:
        artifacts = manifest.get("artifacts", [])
        batch_id = manifest["batchId"]
        return GeneratedReportItem(
            batchId=batch_id,
            reportId=manifest.get("reportId", "unknown"),
            reportName=manifest.get("reportName", "Generated Report"),
            reportType=manifest.get("reportType") or self._report_type_label(manifest.get("reportId", "")),
            generatedAt=manifest.get("generatedAt", ""),
            status=manifest.get("status", "completed"),
            excelDownloadUrl=self._artifact_url(batch_id, "excel", artifacts),
            pdfDownloadUrl=self._artifact_url(batch_id, "pdf", artifacts),
            excelSize=self._artifact_size(artifacts, "excel"),
            pdfSize=self._artifact_size(artifacts, "pdf"),
        )

    def _discover_artifacts(self, batch_id: str, batch_dir: Path) -> list[dict]:
        artifacts: list[dict] = []
        for path in batch_dir.iterdir():
            if not path.is_file() or path.name == "manifest.json":
                continue
            suffix = path.suffix.lower()
            if suffix == ".xlsx":
                artifacts.append(self._artifact(batch_id, "excel", path.name, path).model_dump(by_alias=True))
            elif suffix == ".pdf":
                artifacts.append(self._artifact(batch_id, "pdf", path.name, path).model_dump(by_alias=True))
            elif suffix == ".csv":
                artifacts.append(self._artifact(batch_id, "csv", path.name, path).model_dump(by_alias=True))
            elif suffix == ".json":
                artifacts.append(
                    self._artifact(batch_id, "dashboard_json", path.name, path).model_dump(by_alias=True)
                )
        return artifacts

    def _infer_report_id(self, batch_dir: Path) -> str:
        for path in batch_dir.iterdir():
            if path.suffix.lower() in {".xlsx", ".pdf", ".json"}:
                parsed = self._parse_report_id_from_filename(path.name)
                if parsed:
                    return parsed
        return "unknown"

    @staticmethod
    def _parse_report_id_from_filename(filename: str) -> str | None:
        stem = Path(filename).stem
        parts = stem.rsplit("_", 1)
        if len(parts) == 2 and parts[1]:
            return parts[1]
        return None

    @staticmethod
    def _artifact_url(batch_id: str, format: str, artifacts: list[dict]) -> str | None:
        if any(artifact.get("format") == format for artifact in artifacts):
            return f"/api/v1/outputs/{batch_id}/download?format={format}"
        return None

    @staticmethod
    def _artifact_size(artifacts: list[dict], format: str) -> int | None:
        for artifact in artifacts:
            if artifact.get("format") == format:
                return artifact.get("size")
        return None

    @staticmethod
    def _resolve_status(artifacts: list) -> str:
        formats = set()
        for artifact in artifacts:
            fmt = artifact.format if hasattr(artifact, "format") else artifact.get("format")
            if fmt in {"excel", "pdf", "csv"}:
                formats.add(fmt)
        if {"excel", "pdf"}.issubset(formats) or (formats and "csv" in formats and len(formats) >= 2):
            return "completed"
        if formats:
            return "partial"
        return "failed"

    @staticmethod
    def _report_type_label(report_id: str) -> str:
        return REPORT_TYPE_LABELS.get(report_id, report_id.replace("-", " ").title())

    @staticmethod
    def _artifact(batch_id: str, format: str, filename: str, path: Path) -> OutputArtifact:
        return OutputArtifact(
            format=format,
            filename=filename,
            path=str(path),
            downloadUrl=f"/api/v1/outputs/{batch_id}/download?format={format}",
            size=path.stat().st_size,
        )

    @staticmethod
    def _build_filename(report_name: str, report_id: str, extension: str) -> str:
        safe_name = re.sub(r"[^\w\-]+", "_", report_name.lower()).strip("_") or "report"
        date_str = datetime.now(UTC).strftime("%Y%m%d")
        return f"{safe_name}_{date_str}_{report_id}.{extension}"

    @staticmethod
    def _resolve_report_name(report_id: str) -> str:
        rule_set = get_report_rules(report_id)
        if rule_set:
            return rule_set.report_name
        return report_id
