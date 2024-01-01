import pytest
from typing import List
from csv_converter import IsracardConverter, IsracardRow


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
    assert rows[0] == ["04/07/2023", "AMAZON", "4623", "Transaction date: 03/07/2023. Original amt: USD123", 'N/A']


@pytest.mark.parametrize(('in_row', 'out_row'), [
    [["04/07/2023", "AMAZON", "4623", "Transaction date: 03/07/2023", 'N/A'], {'Amount': -4623.0, 'Date': '2023-07-04', 'Memo': 'Transaction date: 03/07/2023', 'Payee': 'AMAZON'}],
    [["04/07/2023", "AMAZON", "-4623.5", "Transaction date: 03/07/2023", 'N/A'], {'Amount': 4623.5, 'Date': '2023-07-04', 'Memo': 'Transaction date: 03/07/2023', 'Payee': 'AMAZON'}],
])
def test_isracard_row(in_row, out_row):
    irow = IsracardRow(in_row)
    assert irow.serialize() == out_row


@pytest.mark.parametrize(('memo', 'payment_num'), [
    ['blah', None],
    ['תשלום 1 מתוך adsdf', None],
    ['תשלום 1 מתוך 3', 1],
    ['תשלום 2 מתוך 3', 2],
    [None, None],  # memo can be None sometimes
])
def test_get_payment_num(memo, payment_num):
    row = IsracardRow(['', '', '', memo, ''])
    assert row._get_payment_num() == payment_num


@pytest.mark.parametrize(('in_date', 'n_months', 'out_date'), [
    ['01/01/1970', 2, '01/03/1970'],
    ['01/01/1970', 0, '01/01/1970'],
])
def test_add_n_months_to_date(in_date, n_months, out_date):
    row = IsracardRow([in_date, '', '', '', ''])
    assert row._add_n_months_to_date(n_months) == out_date
