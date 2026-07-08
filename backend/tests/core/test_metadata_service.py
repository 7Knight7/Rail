import pytest
from openpyxl import Workbook

from app.core.spreadsheet.excel_reader import ExcelReader
from app.core.spreadsheet.metadata_service import DatasetMetadataService


@pytest.fixture
def sample_dataset(tmp_path):
    path = tmp_path / "zone_report.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Grievance ID", "Zone", "Current Status", "Remarks"])
    sheet.append(["GRV-1", "SCR", "Closed", None])
    sheet.append(["GRV-2", "SCR", "Open", ""])
    sheet.append(["GRV-3", "NCR", "Closed", "Resolved"])
    workbook.save(path)
    workbook.close()
    return ExcelReader().read(path)


def test_generate_metadata_returns_columns_separate_from_rows(sample_dataset):
    service = DatasetMetadataService()
    result = service.split(sample_dataset)

    assert len(result.rows) == 3
    assert result.rows[0][0] == "GRV-1"
    assert len(result.metadata.columns) == 4
    assert "rows" not in result.metadata.to_dict()


def test_generate_metadata_includes_required_fields(sample_dataset):
    metadata = DatasetMetadataService().generate(sample_dataset)
    zone = next(column for column in metadata.columns if column.name == "Zone")

    assert zone.name == "Zone"
    assert zone.data_type == "text"
    assert zone.nullable is False
    assert zone.unique_values == ["SCR", "NCR"]
    assert zone.unique_value_count == 2
    assert zone.filterable is True
    assert zone.sortable is True


def test_generate_metadata_detects_nullable_columns(sample_dataset):
    metadata = DatasetMetadataService().generate(sample_dataset)
    remarks = next(column for column in metadata.columns if column.name == "Remarks")

    assert remarks.nullable is True
    assert remarks.unique_values == ["Resolved"]
    assert remarks.unique_value_count == 1


def test_generate_metadata_caps_unique_values(tmp_path):
    path = tmp_path / "large_unique.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Code"])
    for index in range(60):
        sheet.append([f"VAL-{index}"])
    workbook.save(path)
    workbook.close()

    dataset = ExcelReader().read(path)
    metadata = DatasetMetadataService(unique_value_limit=10).generate(dataset)
    code = metadata.columns[0]

    assert code.unique_value_count == 60
    assert len(code.unique_values) == 10


def test_generate_metadata_preserves_source_file_info(sample_dataset):
    metadata = DatasetMetadataService().generate(sample_dataset)

    assert metadata.source.filename == "zone_report.xlsx"
    assert metadata.row_count == 3
    assert metadata.column_count == 4
