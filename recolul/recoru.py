from dataclasses import dataclass
from typing import TypeAlias

import requests
from bs4 import BeautifulSoup, Tag
from requests import Session


@dataclass
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


@dataclass
class ChartRow:
    """Row of the attendance chart"""
    def __init__(self, tag: Tag):
        self._tag = tag

    def __getitem__(self, i) -> ChartEntry:
        column = self._tag.select_one(f"td:nth-child({i + 1})", recursive=False)
        return ChartEntry(column)

    @property
    def day(self) -> ChartEntry:
        return self[0]

    @property
    def clock_in_time(self) -> str:
        return self[3].text

    @property
    def clock_out_time(self) -> str:
        return self[4].text


AttendanceChart: TypeAlias = list[ChartRow]


class RecoruSession:
    def __init__(self, contract_id: str, auth_id: str, password: str):
        self._contract_id: str = contract_id
        self._auth_id: str = auth_id
        self._password: str = password

        self._session: Session | None = None

    def __enter__(self):
        self._session = requests.Session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close()
        self._session = None

    @property
    def session(self) -> Session:
        assert self._session, "RecoruSession should be used as a context manager"
        return self._session

    def get_attendance_chart(self) -> AttendanceChart:
        self._login()

        response = self.session.post("https://app.recoru.in/ap/home/loadAttendanceChartGadget")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        table_body = soup.select("#ID-attendanceChartGadgetTable > tbody")[0]
        return [
            ChartRow(row)
            for row in table_body.find_all("tr", recursive=False)
        ]

    def _login(self):
        url = "https://app.recoru.in/ap/login"
        form_data = {
            "contractId": self._contract_id,
            "authId": self._auth_id,
            "password": self._password
        }
        response = self.session.post(url, data=form_data)
        response.raise_for_status()
