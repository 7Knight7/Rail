"""Orchestrate dataset loading and report processing."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.core.spreadsheet.excel_reader import ExcelReader
from app.features.datasets.service import DatasetService
from app.features.processing.converters import dataset_from_split
from app.features.processing.engine import ReportProcessingEngine
from app.features.processing.rules.registry import get_report_rules, list_report_rules
from app.features.processing.rules.schemas import ReportRuleSet, ReportRuleSetResponse, ReportRulesConfig


class ReportProcessingService:
    def __init__(self, session: AsyncSession) -> None:
        self._dataset_service = DatasetService(session)
        self._excel_reader = ExcelReader()
        self._engine = ReportProcessingEngine()

    async def process(self, request: ProcessDatasetRequest) -> ProcessDatasetResponse:
        dataset = await self._load_dataset(request)

        if request.configuration:
            result = await self._engine.process(dataset, request.configuration)
        else:
            rules_config = self._resolve_rules_config(request)
            result = await self._engine.process_report_config(dataset, rules_config)

        return self._to_response(result)

    def get_report_rule_set(self, report_id: str) -> ReportRuleSet:
        rule_set = get_report_rules(report_id)
        if not rule_set:
            raise NotFoundError("Report rules", report_id)
        return rule_set

    def list_report_rule_sets(self) -> ReportRuleSetResponse:
        return ReportRuleSetResponse(reports=list_report_rules())

    def _resolve_rules_config(self, request: ProcessDatasetRequest) -> ReportRulesConfig:
        if request.rules:
            return request.rules
        if request.report_id:
            rule_set = get_report_rules(request.report_id)
            if rule_set:
                return rule_set.rules
        raise ValidationError("Either rules, configuration, or a known reportId is required")

    async def process_file(
        self,
        file_path: str | Path,
        configuration: ReportConfiguration,
    ) -> ProcessDatasetResponse:
        split = self._dataset_service.read_with_metadata(Path(file_path))
        dataset = dataset_from_split(split)
        result = await self._engine.process(dataset, configuration)
        return self._to_response(result)

    async def _load_dataset(self, request: ProcessDatasetRequest):
        if request.file_path:
            split = self._dataset_service.read_with_metadata(Path(request.file_path))
            return dataset_from_split(split)

        if request.report_id:
            metadata = await self._dataset_service.get_metadata(request.report_id)
            file_path = await self._dataset_service.get_source_file_path(request.report_id)
            split = self._dataset_service.read_with_metadata(
                file_path,
                header_row=metadata.header_row,
            )
            return dataset_from_split(split)

        raise ValidationError("Either reportId or filePath is required")

    def _to_response(self, result) -> ProcessDatasetResponse:
        highlights = [
            {
                "rowIndex": highlight.row_index,
                "column": highlight.column,
                "backgroundColor": highlight.background_color,
                "textColor": highlight.text_color,
                "bold": highlight.bold,
            }
            for highlight in result.highlights
        ]

        return ProcessDatasetResponse(
            columns=[
                ProcessedColumn(name=column, index=index)
                for index, column in enumerate(result.dataset.columns)
            ],
            rows=result.dataset.rows,
            highlights=highlights,
            rowCount=result.row_count,
            columnCount=result.column_count,
            stepsApplied=result.steps_applied,
            warnings=result.warnings,
        )
