import os.path

from recolul.duration import Duration
from recolul.recoru.attendance_chart import AttendanceChart
from recolul.recoru.recoru_session import RecoruSession
from recolul.time import get_overtime_history

RESOURCES_FOLDER = os.path.realpath(f"{__file__}/../resources")


def load_mock_attendance_chart(filename: str) -> AttendanceChart:
    path = os.path.join(RESOURCES_FOLDER, filename)
    return RecoruSession.read_attendance_chart_file(path)


def test_get_overtime_history_multiple_entry_rows():
    # 8/7: AM WFH, PM in office
    # 8/14: Extra row of WFH
    chart = load_mock_attendance_chart("multiple_entry_rows.html")
    days, overtime_history, total_workplace_times = get_overtime_history(chart)
    assert days == ["8/7(月)", "8/8(火)", "8/9(水)", "8/10(木)", "8/14(月)"]
    assert overtime_history == [
        Duration(45),
        Duration(25),
        Duration(-48),
        Duration.parse("01:31"),
        -Duration.parse("02:19")
    ]
    assert total_workplace_times == {
        "HF Bldg.": (
            Duration.parse("06:58") +
            Duration.parse("08:25") +
            Duration.parse("07:12") +
            Duration.parse("09:31")
        ),
        "WFH": Duration.parse("01:47") + Duration.parse("05:26") + Duration(15)
    }


def test_get_overtime_history_no_work_time():
    # 11/22: No work time
    # 11/23: Holiday
    # 11/24: Paid leave
    chart = load_mock_attendance_chart("unworked_wednesday.html")
    days, overtime_history, total_workplace_times = get_overtime_history(chart)
    assert days == ["11/20(月)", "11/21(火)", "11/22(水)", "11/24(金)"]
    assert overtime_history == [Duration(14), Duration(8), Duration(-8 * 60), Duration(0)]
    assert total_workplace_times == {
        "HF Bldg.": Duration.parse("08:14") + Duration.parse("08:08") + Duration.parse("08:00")
    }


def test_get_overtime_history_worked_holiday():
    chart = load_mock_attendance_chart("worked_holiday.html")
    days, overtime_history, total_workplace_times = get_overtime_history(chart)
    assert days == ["11/20(月)", "11/21(火)", "11/22(水)", "11/23(木)", "11/24(金)"]
    assert overtime_history == [-Duration(2), Duration(17), Duration(19), Duration.parse("03:23"), Duration(4)]
    assert total_workplace_times == {
        "HF Bldg.": (
            Duration.parse("07:58") +
            Duration.parse("08:17") +
            Duration.parse("08:19") +
            Duration.parse("08:04")
        ),
        "WFH": Duration.parse("03:23")
    }
