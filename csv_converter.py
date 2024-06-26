import csv
import re
import pandas as pd
import typer
import math
from typing import List, Union, Optional
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod


DATA_DIR = "/home/nss/Downloads"


class CSVConverter(ABC):

    def __init__(self, rows: List[List[object]]):
        self.rows = rows

    def convert(self, out_filename: str) -> None:
        converted_rows = [row.serialize() for row in self.get_rows_to_convert()]
        write_csv(out_filename, ['Date', 'Payee', 'Memo', 'Amount'], converted_rows)

    @abstractmethod
    def get_rows_to_convert(self) -> List['CSVRow']:
        pass


class CSVRow(ABC):

    fieldnames = []

    def __init__(self, row: List[str]):
        self.row = row
        for idx, fieldname in enumerate(self.fieldnames):
            value = row[idx]
            if isinstance(value, float) and math.isnan(value):
                value = None
            setattr(self, fieldname, value)

    def serialize(self) -> dict:
        return {
            "Date": self.get_date(),
            "Memo": self.get_memo(),
            "Payee": self.get_payee(),
            "Amount": self.get_amount(),
        }

    @abstractmethod
    def get_date(self):
        pass

    @abstractmethod
    def get_memo(self):
        pass

    @abstractmethod
    def get_payee(self):
        pass

    @abstractmethod
    def get_amount(self):
        pass


class PoalimRow(CSVRow):

    fieldnames = ['date', 'action', 'details', 'reference', 'credit', 'debit', 'account_amount', 'date_value',
                  'beneficiary', 'for']
    __slots__ = ['date', 'action', 'details', 'reference', 'credit', 'debit', 'account_amount', 'date_value',
                 'beneficiary', 'for']

    def get_date(self):
        return self.convert_date_string(self.date)

    def get_memo(self):
        return self.details

    def get_payee(self):
        if self.beneficiary:
            return self.beneficiary
        if self.action in {"מסטרקרד", "שיק"}:
            # reference has last 4 digits of card being paid
            return f"{self.action} {self.reference}"
        return self.action

    def get_amount(self):
        return -self.credit if self.credit else self.debit

    @staticmethod
    def convert_date_string(date_obj: datetime) -> str:
        # Assuming input format is dd.mm.yyyy
        return date_obj.strftime("%Y-%m-%d")

    @staticmethod
    def _parse_int_str(int_str: str) -> int:
        return int(int_str.replace(',', ''))


class PoalimConverter(CSVConverter):

    def __init__(self, rows: List[List[str]], *args, **kwargs):
        super().__init__(rows)

    def get_rows_to_convert(self) -> List[CSVRow]:
        return [PoalimRow(row) for row in self.rows[6:]]


class IsracardRow(CSVRow):

    fieldnames = ['date', 'action', 'amount', 'memo', 'transaction_id']
    __slots__ = ['date', 'action', 'amount', 'memo', 'transaction_id']

    def get_amount(self):
        return -float(self.amount)

    def _get_payment_num(self) -> Optional[int]:
        """
        :return: True if this row represents the first payment of a series
        """
        if not self.memo:
            return
        payment_reg = r"תשלום (\d+) מתוך (\d+)"
        match = re.match(payment_reg, self.memo)
        return match and int(match.group(1))

    def get_payee(self):
        payee = self.action
        if "BIT" in payee or "PAYBOX" in payee:
            payee += f" {self.transaction_id}"  # so ynab doesn't auto-match it
        return payee

    def get_memo(self):
        return self.memo

    def get_date(self):
        payment_num = self._get_payment_num()
        date_str = self.date
        if payment_num and payment_num > 1:
            date_str = self._add_n_months_to_date(payment_num-1)
        return self.convert_date_string(date_str)

    def _add_n_months_to_date(self, n_months):
        date_obj = datetime.strptime(self.date, "%d/%m/%Y")
        date_obj = date_obj.replace(month=date_obj.month + n_months)
        return date_obj.strftime("%d/%m/%Y")

    @staticmethod
    def convert_date_string(date_str: str) -> str:
        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
        return date_obj.strftime("%Y-%m-%d")


class IsracardConverter(CSVConverter):

    def __init__(self, rows: List[List[str]], card_number: str):
        super().__init__(rows)
        self.card_number = card_number

    def _get_mastercard_rows(self) -> List[List[object]]:
        rows = []
        is_the_card = False
        is_any_card_reg = re.compile("מסטרקארד - \d+")
        search_phrase = f"מסטרקארד - {self.card_number}"
        for row in self.rows:
            if isinstance(row[0], str):
                if search_phrase in row[0]:
                    is_the_card = True
                    continue
                elif is_any_card_reg.search(row[0]) is not None:
                    # not THE card. some other card
                    is_the_card = False
                    continue
            if is_the_card:
                rows += [row]
        return rows

    @staticmethod
    def _has_valid_date(row: List[str]) -> bool:
        try:
            IsracardRow.convert_date_string(row[0])
            return True
        except (ValueError, TypeError):
            return False

    def _get_israel_charges(self) -> List[List[str]]:
        rows = self._get_mastercard_rows()
        charges = []
        is_israel = False
        for row in rows:
            if row[0].startswith("עסקאות בארץ"):
                is_israel = True
                continue
            elif row[1].startswith("סך חיוב"):
                break
            if not is_israel or not self._has_valid_date(row):
                continue
            charges += [[
                row[0], row[1], row[4], row[7], row[6]  # date, name, amount, memo, ID
            ]]
        return charges

    def _get_foreign_charges(self) -> List[List[object]]:
        rows = self._get_mastercard_rows()
        charges = []
        is_foreign = False
        for row in rows:
            if isinstance(row[0], str) and row[0].startswith("עסקאות בחו˝ל"):
                is_foreign = True
                continue
            if not is_foreign or not self._has_valid_date(row):
                continue
            charges += [[
                row[1], row[2], row[5], f"Transaction date: {row[0]}. Original amt: {row[4]}{row[3]}", "N/A"  # date, name, amount, memo, ID
            ]]
        return charges

    def get_rows_to_convert(self) -> List[CSVRow]:
        return [IsracardRow(row) for row in (self._get_israel_charges() + self._get_foreign_charges())]


class CSVConverterFactory:

    format2converter = {
        "poalim": PoalimConverter,
        "isracard": IsracardConverter,
    }

    @classmethod
    def create(cls, source: str, *converter_args, **converter_kwargs) -> CSVConverter:
        return cls.format2converter.get(source)(*converter_args, **converter_kwargs)


def read_data_file(filename: Union[str, Path]) -> List[List[object]]:
    if isinstance(filename, str):
        filename = Path(filename)
    if filename.suffix.lower() in {'.xlsx', '.xls'}:
        data = pd.read_excel(filename).values.tolist()
        assert isinstance(data, list)
        return data
    elif filename.suffix.lower() == ".csv":
        with open(filename, 'r') as fin:
            return list(csv.reader(fin))
    else:
        raise RuntimeError(f"Unknown file type for file '{filename}'")


def write_csv(filename: Union[str, Path], header_rows: List[str], rows: List[dict]) -> None:
    with open(filename, 'w') as fout:
        cout = csv.DictWriter(fout, header_rows)
        cout.writeheader()
        cout.writerows(rows)


def convert_csv(in_filename: str, out_filename: str, source: str, card_number: str) -> None:
    rows = read_data_file(f"{DATA_DIR}/{in_filename}")
    converter = CSVConverterFactory.create(source, rows, card_number)
    converter.convert(out_filename)


if __name__ == '__main__':
    typer.run(convert_csv)

