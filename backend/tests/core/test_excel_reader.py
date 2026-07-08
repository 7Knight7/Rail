import pytest
from openpyxl import Workbook

from app.core.exceptions import ValidationError
from app.core.spreadsheet.excel_reader import ExcelReader, read_excel_file


@pytest.fixture
def sample_workbook(tmp_path):
    path = tmp_path / "zone_report.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "RailMadad Data"
    sheet.append(
        [
            "Grievance ID",
            "Zone",
            "Division",
            "Train No",
            "Registration Date",
            "Current Status",
        ]
    )
    sheet.append(
        [
            "GRV-10001",
            "SCR",
            "Hyderabad",
            12713,
            "2026-07-01",
            "Closed",
        ]
    )
    sheet.append(
        [
            "GRV-10002",
            "SCR",
            "Secunderabad",
            12714,
            "2026-07-02",
            "Open",
        ]
    )
    workbook.save(path)
    workbook.close()
    return path


def test_read_excel_file_returns_original_columns_and_rows(sample_workbook):
    dataset = read_excel_file(sample_workbook)

    assert [column.name for column in dataset.columns] == [
        "Grievance ID",
        "Zone",
        "Division",
        "Train No",
        "Registration Date",
        "Current Status",
    ]
    assert len(dataset.rows) == 2
    assert dataset.rows[0] == [
        "GRV-10001",
        "SCR",
        "Hyderabad",
        12713,
        "2026-07-01",
        "Closed",
    ]
    assert dataset.rows[1][0] == "GRV-10002"


def test_read_excel_file_preserves_all_columns_including_empty_headers(tmp_path):
    path = tmp_path / "partial_headers.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Grievance ID", "", "Zone"])
    sheet.append(["GRV-1", "ignored", "SCR"])
    workbook.save(path)
    workbook.close()

    dataset = ExcelReader().read(path)

    assert [column.name for column in dataset.columns] == ["Grievance ID", "", "Zone"]
    assert dataset.rows[0] == ["GRV-1", "ignored", "SCR"]


def test_read_excel_file_infers_column_types(sample_workbook):
    dataset = read_excel_file(sample_workbook)

    types = {column.name: column.data_type for column in dataset.columns}
    assert types["Grievance ID"] == "text"
    assert types["Train No"] == "number"
    assert types["Registration Date"] == "date"
    assert types["Current Status"] == "status"


def test_read_excel_file_metadata(sample_workbook):
    dataset = read_excel_file(sample_workbook)

    assert dataset.metadata.filename == "zone_report.xlsx"
    assert dataset.metadata.sheet_name == "RailMadad Data"
    assert dataset.metadata.header_row == 1
    assert dataset.metadata.row_count == 2
    assert dataset.metadata.column_count == 6


def test_read_excel_file_to_dict_shape(sample_workbook):
    payload = read_excel_file(sample_workbook).to_dict()

    assert set(payload.keys()) == {"columns", "rows", "metadata"}
    assert payload["columns"][0]["name"] == "Grievance ID"
    assert payload["columns"][0]["display_name"] == "Grievance ID"
    assert payload["rows"][1][3] == 12714


def test_read_excel_file_missing_path_raises():
    with pytest.raises(ValidationError, match="Excel file not found"):
        read_excel_file("downloads/missing.xlsx")


def test_read_excel_file_unsupported_format_raises(tmp_path):
    path = tmp_path / "zone_report.csv"
    path.write_text("a,b\n1,2", encoding="utf-8")

    with pytest.raises(ValidationError, match="Unsupported Excel format"):
        read_excel_file(path)
