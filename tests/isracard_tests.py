import pytest
from typing import List
from csv_converter import IsracardConverter


@pytest.fixture
def normal_isracard_rows() -> List[List[str]]:
    return [
        ["Noah Santacruz", "", "", ""],
        ["", "", "", ""],
        ["דירקט - 1234 בלה", "", "", ""],
        ["עסקאות בארץ", "", "", ""],
        ["תאריך רכישה", "", "", ""],
        ["23/07/2023", "פועלים- דמי כרטיס"],
        ["", "", "", ""],
        ["מסטרקארד - ", "", "", ""],
        ["עסקאות בארץ", "", "", ""],
        ["תאריך רכישה", "", "", ""],
        ["02/07/2023", "shuk hair", "454", "NIS", "454", "NIS", "123456", "yo"],
        ["03/07/2023", "PAYBOX", "454", "NIS", "-45", "NIS", "123456", "yo"],
        ["03/07/2023", "booze", "454", "NIS", "5000", "NIS", "123456", ""],
        ["05/07/2023", 'סך חיוב בש"ח:', "05/07/2023", "", "15000", "NIS", "", ""],
        ["עסקאות בחו˝ל", "", "", ""],
        ["תאריך רכישה", "", "", ""],
        ["03/07/2023", "04/07/2023", "AMAZON", "123", "USD", "4623", "NIS", ""],
        ["", "04/07/2023", "TOTAL FOR DATE", "4623", "NIS", "", "", ""],
    ]


def test_get_mastercard_rows(normal_isracard_rows):
    conv = IsracardConverter(normal_isracard_rows)
    rows = conv._get_mastercard_rows()
    assert len(rows) == 10
    assert rows[0][0] == "עסקאות בארץ"


def test_get_israel_charges(normal_isracard_rows):
    conv = IsracardConverter(normal_isracard_rows)
    rows = conv._get_israel_charges()
    assert len(rows) == 3
    assert rows[0][0] == "02/07/2023"
    assert rows[0][1] == "shuk hair"


def test_get_foreign_charges(normal_isracard_rows):
    conv = IsracardConverter(normal_isracard_rows)
    rows = conv._get_foreign_charges()
    assert len(rows) == 1
    assert rows[0] == ["04/07/2023", "AMAZON", "4623", "Transaction date: 03/07/2023"]
