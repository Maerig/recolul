import re
from enum import Enum
from typing import TypeAlias

from bs4 import Tag


class ChartColumn(str, Enum):
    DATE = "日付"
    WORKPLACE = "作業場所"
    CATEGORY = "勤務区分"
    START = "開始"
    END = "終了"
    WORK_TIME = "労働時間"
    MEMO = "メモ"


class ChartEntry:
    """Single cell of the attendance chart"""
    def __init__(self, tag: Tag):
        self._tag = tag

    @property
    def text(self) -> str:
        return self._tag.text.strip()

    @property
    def color(self) -> str:
        label = self._tag.find("label", recursive=False)
        if not label:
            return ""
        return label.attrs\
            .get("style", "")\
            .removeprefix("color: ")\
            .removesuffix(";")


class ChartHeader:
    """Header of the attendance chart"""
    def __init__(self, tag: Tag):
        self._column_indices: dict[ChartColumn, int] = {
            ChartEntry(column).text.strip(): i
            for i, column in enumerate(tag.find_all("td", recursive=False))
        }

    def get_column_index(self, column: ChartColumn) -> int:
        return self._column_indices[column]

    def has_column(self, column: ChartColumn) -> bool:
        return column in self._column_indices


class ChartRow:
    """Row of the attendance chart"""
    _date_regex = re.compile(r"^(\d{1,2})\/(\d{1,2})\(.\)$")

    def __init__(self, header: ChartHeader, tag: Tag):
        self._header = header
        self._tag = tag

    def __getitem__(self, column: ChartColumn) -> ChartEntry:
        column_index = self._header.get_column_index(column)
        column = self._tag.select_one(f"td:nth-child({column_index + 1})", recursive=False)
        return ChartEntry(column)

    @property
    def day(self) -> ChartEntry:
        return self[ChartColumn.DATE]

    @property
    def day_of_month(self) -> int:
        match = ChartRow._date_regex.match(self.day.text)
        if not match:
            return 0
        return int(match.group(2))

    @property
    def workplace(self) -> ChartEntry:
        return self[ChartColumn.WORKPLACE]

    @property
    def clock_in_time(self) -> str:
        return self[ChartColumn.START].text

    @property
    def clock_out_time(self) -> str:
        return self[ChartColumn.END].text

    @property
    def work_time(self) -> str:
        return self[ChartColumn.WORK_TIME].text

    @property
    def memo(self) -> str:
        return self[ChartColumn.MEMO].text


AttendanceChart: TypeAlias = list[ChartRow]
