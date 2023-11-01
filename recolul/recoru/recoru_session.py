import requests
from bs4 import BeautifulSoup

from recolul.recoru.attendance_chart import AttendanceChart, ChartHeader, ChartRow, ChartRowEntry


class RecoruSession:
    def __init__(self, contract_id: str, auth_id: str, password: str):
        self._contract_id: str = contract_id
        self._auth_id: str = auth_id
        self._password: str = password

        self._session: requests.Session | None = None

    def __enter__(self):
        self._session = requests.Session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close()
        self._session = None

    @property
    def session(self) -> requests.Session:
        assert self._session, "RecoruSession should be used as a context manager"
        return self._session

    def get_attendance_chart(self) -> AttendanceChart:
        self._login()

        response = self.session.post("https://app.recoru.in/ap/home/loadAttendanceChartGadget")
        response.raise_for_status()
        return self._parse_attendance_chart(response.text)

    @classmethod
    def read_attendance_chart_file(cls, path: str) -> AttendanceChart:
        """Used for testing"""

        with open(path, "rt") as attendance_chart_file:
            text = attendance_chart_file.read()
        return cls._parse_attendance_chart(text)

    def _login(self):
        url = "https://app.recoru.in/ap/login"
        form_data = {
            "contractId": self._contract_id,
            "authId": self._auth_id,
            "password": self._password
        }
        response = self.session.post(url, data=form_data)
        response.raise_for_status()

    @staticmethod
    def _parse_attendance_chart(text: str) -> AttendanceChart:
        soup = BeautifulSoup(text, "html.parser")
        table = soup.select_one("#ID-attendanceChartGadgetTable")

        table_header = table.select_one("thead > tr", recursive=False)
        header = ChartHeader(table_header)

        chart_rows = []
        current_row_entries = []
        table_body = table.find("tbody", recursive=False)
        for row in table_body.find_all("tr", recursive=False):
            entry = ChartRowEntry(header, row)
            if entry.day.text:  # New row
                # Append previous row
                if current_row_entries:
                    chart_rows.append(ChartRow(current_row_entries))
                current_row_entries = [entry]
            else:  # Row with multiple entries
                current_row_entries.append(entry)
        if current_row_entries:
            chart_rows.append(ChartRow(current_row_entries))
        return chart_rows
