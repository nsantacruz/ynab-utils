import csv
import pandas as pd
import typer
import math
from typing import List
from datetime import datetime
from abc import ABC, abstractmethod


DATA_DIR = "/Users/nss/Downloads"


class CSVConverter(ABC):

    def __init__(self, in_filename: str):
        self.rows = read_data_file(f"{DATA_DIR}/{in_filename}")

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

    def __init__(self, in_filename: str):
        super().__init__(in_filename)

    def get_rows_to_convert(self) -> List[CSVRow]:
        return [PoalimRow(row) for row in self.rows[6:]]


class CSVConverterFactory:

    format2converter = {
        "poalim": PoalimConverter
    }

    @classmethod
    def create(cls, source: str, *converter_args, **converter_kwargs) -> CSVConverter:
        return cls.format2converter.get(source)(*converter_args, **converter_kwargs)


def read_data_file(filename: str) -> List[List[object]]:
    if filename.endswith(".xlsx"):
        data = pd.read_excel(filename).values.tolist()
        assert isinstance(data, list)
        return data
    elif filename.endswith(".csv"):
        with open(filename, 'r') as fin:
            return list(csv.reader(fin))
    else:
        raise RuntimeError(f"Unknown file type for file '{filename}'")


def write_csv(filename: str, header_rows: List[str], rows: List[dict]) -> None:
    with open(filename, 'w') as fout:
        cout = csv.DictWriter(fout, header_rows)
        cout.writeheader()
        cout.writerows(rows)


def convert_csv(in_filename: str, out_filename: str, source: str) -> None:
    converter = CSVConverterFactory.create(source, in_filename)
    converter.convert(out_filename)


if __name__ == '__main__':
    typer.run(convert_csv)

