from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QWidget

from gui.this_month import ThisMonth
from gui.today import Today
from recolul.recoru.attendance_chart import AttendanceChart


class Summary(QWidget):
    def __init__(self, full_attendance_chart: AttendanceChart, parent: QWidget | None = None):
        super().__init__(parent)

        self.this_month = ThisMonth(full_attendance_chart, self)
        self.today = Today(full_attendance_chart, self)

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.this_month)
        self.layout.addWidget(self.today)

        # Refresh every minute
        timer = QTimer(self)
        timer.setInterval(60_000)
        timer.timeout.connect(self.refresh)
        timer.start()

    def refresh(self):
        self.this_month.update_text()
        self.today.update_text()
