import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.core.spreadsheet.excel_reader import ExcelReader
from app.core.spreadsheet.metadata_service import DatasetMetadataService
from app.features.datasets.schemas import ColumnMetadata, DatasetMetadataResponse
from app.features.uploads.service import UploadService
from app.infrastructure.database.models import ReportDatasetModel

logger = logging.getLogger(__name__)

SUPPORTED_REPORT_IDS = frozenset(
    {"merging", "division", "train-no", "types", "scr-train", "scr-station"}
)


class DatasetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_report_id(self, report_id: str) -> ReportDatasetModel | None:
        result = await self._session.execute(
            select(ReportDatasetModel).where(ReportDatasetModel.report_id == report_id).limit(1)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        report_id: str,
        source_filename: str,
        source_file_path: str | None,
        header_row: int,
        row_count: int,
        columns: list[ColumnMetadata],
    ) -> ReportDatasetModel:
        existing = await self.get_by_report_id(report_id)
        payload = json.dumps([column.model_dump(by_alias=True) for column in columns])

        if existing:
            existing.source_filename = source_filename
            existing.source_file_path = source_file_path
            existing.header_row = header_row
            existing.row_count = row_count
            existing.columns_json = payload
            existing.parsed_at = datetime.now(UTC)
            await self._session.commit()
            await self._session.refresh(existing)
            return existing

        model = ReportDatasetModel(
            report_id=report_id,
            source_filename=source_filename,
            source_file_path=source_file_path,
            header_row=header_row,
            row_count=row_count,
            columns_json=payload,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return model


class DatasetService:
    def __init__(self, session: AsyncSession, upload_service: UploadService | None = None) -> None:
        self._repository = DatasetRepository(session)
        self._upload_service = upload_service or UploadService()
        self._excel_reader = ExcelReader()
        self._metadata_service = DatasetMetadataService()

    def _validate_report_id(self, report_id: str) -> None:
        if report_id not in SUPPORTED_REPORT_IDS:
            raise NotFoundError("Report dataset", report_id)

    def _to_response(self, model: ReportDatasetModel) -> DatasetMetadataResponse:
        columns_data = json.loads(model.columns_json)
        return DatasetMetadataResponse(
            reportId=model.report_id,
            sourceFilename=model.source_filename,
            headerRow=model.header_row,
            rowCount=model.row_count,
            columns=[ColumnMetadata.model_validate(item) for item in columns_data],
            parsedAt=model.parsed_at.isoformat(),
        )

    async def get_source_file_path(self, report_id: str) -> Path:
        self._validate_report_id(report_id)
        model = await self._repository.get_by_report_id(report_id)
        if not model or not model.source_file_path:
            raise NotFoundError("Dataset source file", report_id)

        file_path = Path(model.source_file_path)
        if not file_path.exists():
            raise NotFoundError("Dataset source file", str(file_path))
        return file_path

    async def get_metadata(self, report_id: str) -> DatasetMetadataResponse:
        self._validate_report_id(report_id)
        model = await self._repository.get_by_report_id(report_id)
        if not model:
            raise NotFoundError("Report dataset", report_id)
        return self._to_response(model)

    async def ingest_upload(
        self,
        report_id: str,
        *,
        upload_id: str,
        header_row: int = 1,
        sheet_name: str | None = None,
    ) -> DatasetMetadataResponse:
        self._validate_report_id(report_id)

        for extension in (".xlsx", ".xls", ".csv"):
            try:
                file_path = await self._upload_service.get_file_path(upload_id, extension)
                break
            except ValidationError:
                file_path = None
        else:
            raise NotFoundError("Upload", upload_id)

        dataset = self._excel_reader.read(file_path, header_row=header_row, sheet_name=sheet_name)
        return await self._persist_dataset(
            report_id=report_id,
            dataset=dataset,
            source_filename=file_path.name,
            source_file_path=str(file_path),
            header_row=header_row,
        )

    async def ingest_file(
        self,
        report_id: str,
        *,
        file_path: Path,
        source_filename: str,
        header_row: int = 1,
        sheet_name: str | None = None,
    ) -> DatasetMetadataResponse:
        self._validate_report_id(report_id)

        dataset = self._excel_reader.read(file_path, header_row=header_row, sheet_name=sheet_name)
        return await self._persist_dataset(
            report_id=report_id,
            dataset=dataset,
            source_filename=source_filename,
            source_file_path=str(file_path),
            header_row=header_row,
        )

    async def _persist_dataset(
        self,
        *,
        report_id: str,
        dataset,
        source_filename: str,
        source_file_path: str,
        header_row: int,
    ) -> DatasetMetadataResponse:
        generated = self._metadata_service.generate(dataset)
        columns = [
            ColumnMetadata(
                id=column.id,
                fieldName=column.name,
                displayName=column.name,
                dataType=column.data_type,
                nullable=column.nullable,
                uniqueValues=column.unique_values,
                uniqueValueCount=column.unique_value_count,
                filterable=column.filterable,
                sortable=column.sortable,
            )
            for column in generated.columns
        ]

        model = await self._repository.upsert(
            report_id=report_id,
            source_filename=source_filename,
            source_file_path=source_file_path,
            header_row=header_row,
            row_count=generated.row_count,
            columns=columns,
        )
        logger.info("Ingested dataset metadata for report %s (%s columns)", report_id, len(columns))
        return self._to_response(model)

    def read_with_metadata(
        self,
        file_path: Path,
        *,
        header_row: int = 1,
        sheet_name: str | None = None,
    ):
        """Read an Excel file and return rows separately from generated metadata."""
        dataset = self._excel_reader.read(file_path, header_row=header_row, sheet_name=sheet_name)
        return self._metadata_service.split(dataset)
