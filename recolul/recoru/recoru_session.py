import requests
from bs4 import BeautifulSoup

from recolul.recoru.attendance_chart import AttendanceChart, ChartHeader, ChartRow


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
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.select_one("#ID-attendanceChartGadgetTable")

        table_header = table.select_one("thead > tr", recursive=False)
        header = ChartHeader(table_header)

        table_body = table.find("tbody", recursive=False)
        return [
            ChartRow(header, row)
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
