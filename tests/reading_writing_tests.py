import pytest
import csv
import shutil
from pathlib import Path
import pandas as pd
from csv_converter import write_csv, read_data_file


@pytest.fixture
def tmp_path() -> Path:
    return Path("tmp")


@pytest.fixture
def sample_data():
    header_rows = ["Name", "Age", "City"]
    rows = [
        {"Name": "John", "Age": 25, "City": "New York"},
        {"Name": "Alice", "Age": 30, "City": "San Francisco"},
        {"Name": "Bob", "Age": 22, "City": "Los Angeles"},
    ]
    return header_rows, rows


@pytest.fixture(autouse=True)
def create_and_cleanup_tmp_path(request, tmp_path: Path):
    if not tmp_path.exists():
        tmp_path.mkdir()

    yield

    if tmp_path.exists() and tmp_path.is_dir():
        shutil.rmtree(tmp_path)


def test_write_csv(tmp_path, sample_data):
    header_rows, rows = sample_data
    filename = tmp_path / "test_output.csv"

    # Call the function
    write_csv(filename, header_rows, rows)

    # Read the written CSV file
    with open(filename, 'r') as fin:
        reader = csv.reader(fin)
        actual_rows = list(reader)

    # Assert the header and data rows
    assert actual_rows[0] == header_rows
    assert actual_rows[1:] == [[str(row[key]) for key in header_rows] for row in rows]


def test_write_csv_empty(tmp_path):
    # Test writing an empty CSV file
    filename = tmp_path / "empty_output.csv"
    write_csv(filename, [], [])

    # Read the written CSV file
    with open(filename, 'r') as fin:
        reader = csv.reader(fin)
        actual_rows = list(reader)

    # Assert that the file is empty
    assert actual_rows == [[]]


@pytest.fixture
def excel_file(tmp_path):
    data = [
        ["Name", "Age", "City"],
        ["John", 25, "New York"],
        ["Alice", 30, "San Francisco"],
        ["Bob", 22, "Los Angeles"]
    ]
    filename = tmp_path / "test_data.xlsx"
    df = pd.DataFrame(data, columns=["Name", "Age", "City"])
    df.to_excel(filename, index=False)
    return filename


@pytest.fixture
def csv_file(tmp_path):
    data = [
        ["Name", "Age", "City"],
        ["John", 25, "New York"],
        ["Alice", 30, "San Francisco"],
        ["Bob", 22, "Los Angeles"]
    ]
    filename = tmp_path / "test_data.csv"
    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerows(data)
    return filename


def test_read_excel_file(excel_file):
    # Call the function
    data = read_data_file(excel_file)

    # Assert the correctness of the data
    assert isinstance(data, list)
    assert data == [
        ["Name", "Age", "City"],
        ["John", 25, "New York"],
        ["Alice", 30, "San Francisco"],
        ["Bob", 22, "Los Angeles"]
    ]


def test_read_csv_file(csv_file):
    # Call the function
    data = read_data_file(csv_file)

    # Assert the correctness of the data
    assert isinstance(data, list)
    assert data == [
        ["Name", "Age", "City"],
        ["John", '25', "New York"],
        ["Alice", '30', "San Francisco"],
        ["Bob", '22', "Los Angeles"]
    ]


def test_unknown_file_type(tmp_path):
    # Test handling of an unknown file type
    unknown_file = tmp_path / "unknown_file.txt"
    with open(unknown_file, 'w') as file:
        file.write("This is a test")

    with pytest.raises(RuntimeError, match=r"Unknown file type for file"):
        read_data_file(unknown_file)
