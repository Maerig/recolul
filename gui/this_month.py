from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPlainTextEdit, QVBoxLayout, QWidget

from recolul.duration import Duration
from recolul.recoru.attendance_chart import AttendanceChart
from recolul.time import count_working_days, get_overtime_balance, until_today


class ThisMonth(QWidget):
    def __init__(self, full_attendance_chart: AttendanceChart, parent: QWidget | None = None):
        super().__init__(parent)
        self._full_attendance_chart = full_attendance_chart

        self._text_edit = QPlainTextEdit()
        self._text_edit.setReadOnly(True)

        label = QLabel("This month", self)

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._layout.addWidget(self._text_edit)

        self.update_text()

    def update_text(self):
        attendance_chart = until_today(self._full_attendance_chart)
        overtime_balance, total_workplace_times = get_overtime_balance(attendance_chart)
        text = f"Overtime balance: {overtime_balance}\n"
        text += f"Total time per workplace:\n"
        for workplace, total_work_time in total_workplace_times.items():
            text += f"  {workplace}: {total_work_time}\n"
        text += f"Maximum WFH time: {Duration(60) * count_working_days(self._full_attendance_chart)}"
        self._text_edit.setPlainText(text)
