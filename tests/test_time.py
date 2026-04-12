import os.path

from recolul.config import Config
from recolul.duration import Duration
from recolul.recoru.attendance_chart import AttendanceChart
from recolul.recoru.recoru_session import RecoruSession
from recolul.time import LeaveTime, get_leave_time, get_overtime_history

RESOURCES_FOLDER = os.path.realpath(f"{__file__}/../resources")

DEFAULT_CONFIG = Config(recoru_contract_id="", recoru_auth_id="", recoru_password="")
PART_TIME_CONFIG = Config(recoru_contract_id="", recoru_auth_id="", recoru_password="", hours_per_day=6, wfh_hours_per_day=0.5)


def load_mock_attendance_chart(filename: str) -> AttendanceChart:
    path = os.path.join(RESOURCES_FOLDER, filename)
    return RecoruSession.read_attendance_chart_file(path)


def test_get_overtime_history_multiple_entry_rows():
    # 8/7: AM WFH, PM in office
    # 8/14: Extra row of WFH
    chart = load_mock_attendance_chart("multiple_entry_rows.html")
    days, overtime_history, total_workplace_times = get_overtime_history(chart, DEFAULT_CONFIG)
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


def test_get_overtime_history_multiple_entry_rows_part_time():
    # Same fixture but with 6h/day: required time drops by 2h per day,
    # so each day gets +120min overtime compared to 8h.
    chart = load_mock_attendance_chart("multiple_entry_rows.html")
    days, overtime_history, total_workplace_times = get_overtime_history(chart, PART_TIME_CONFIG)
    assert days == ["8/7(月)", "8/8(火)", "8/9(水)", "8/10(木)", "8/14(月)"]
    assert overtime_history == [
        Duration(45 + 120),
        Duration(25 + 120),
        Duration(-48 + 120),
        Duration.parse("01:31") + Duration(120),
        -Duration.parse("02:19") + Duration(120),
    ]
    # Workplace times unchanged (based on actual clock times, not required hours)
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
    days, overtime_history, total_workplace_times = get_overtime_history(chart, DEFAULT_CONFIG)
    assert days == ["11/20(月)", "11/21(火)", "11/22(水)", "11/24(金)"]
    assert overtime_history == [Duration(14), Duration(8), Duration(-8 * 60), Duration(0)]
    assert total_workplace_times == {
        "HF Bldg.": Duration.parse("08:14") + Duration.parse("08:08") + Duration.parse("08:00")
    }


def test_get_overtime_history_no_work_time_part_time():
    # Same fixture with 6h/day: paid leave credits 6h instead of 8h,
    # required time per working day drops to 6h.
    chart = load_mock_attendance_chart("unworked_wednesday.html")
    days, overtime_history, total_workplace_times = get_overtime_history(chart, PART_TIME_CONFIG)
    assert days == ["11/20(月)", "11/21(火)", "11/22(水)", "11/24(金)"]
    assert overtime_history == [
        Duration(14 + 120),       # 08:14 worked - 06:00 required
        Duration(8 + 120),        # 08:08 worked - 06:00 required
        Duration(-6 * 60),        # 0 worked - 06:00 required
        Duration(0),              # 06:00 paid leave - 06:00 required
    ]
    # Paid leave now credits 6h instead of 8h
    assert total_workplace_times == {
        "HF Bldg.": Duration.parse("08:14") + Duration.parse("08:08") + Duration.parse("06:00")
    }


def test_get_overtime_history_worked_holiday():
    chart = load_mock_attendance_chart("worked_holiday.html")
    days, overtime_history, total_workplace_times = get_overtime_history(chart, DEFAULT_CONFIG)
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


def test_clock_out_after_midnight():
    chart = load_mock_attendance_chart("clock_out_after_midnight.html")
    days, overtime_history, total_workplace_times = get_overtime_history(chart, DEFAULT_CONFIG)
    assert days == ["12/1(金)", "12/2(土)", "12/3(日)"]
    assert overtime_history == [Duration.parse("06:11"), Duration.parse("03:00"), Duration.parse("02:17")]
    assert total_workplace_times == {
        "HF Bldg.": Duration.parse("08:12"),
        "WFH": Duration.parse("05:59") + Duration.parse("03:00") + Duration.parse("02:17")
    }


def test_leave_time_with_break():
    chart = load_mock_attendance_chart("when_break.html")
    leave_times = get_leave_time(chart, DEFAULT_CONFIG)
    assert leave_times == [
        LeaveTime(includes_break=True, min_time=Duration.parse("18:31"))
    ]


def test_leave_time_no_break():
    chart = load_mock_attendance_chart("when_no_break.html")
    leave_times = get_leave_time(chart, DEFAULT_CONFIG)
    assert leave_times == [
        LeaveTime(includes_break=False, min_time=Duration.parse("13:39"))
    ]


def test_double_leave_time():
    chart = load_mock_attendance_chart("when_double_leave.html")
    leave_times = get_leave_time(chart, DEFAULT_CONFIG)
    assert leave_times == [
        LeaveTime(
            includes_break=False,
            min_time=Duration.parse("14:22"),
            max_time=Duration.parse("15:00"),
        ),
        LeaveTime(includes_break=True, min_time=Duration.parse("15:22")),
    ]


def test_leave_time_wfh_cutoff_time():
    chart = load_mock_attendance_chart("wfh_cutoff_time.html")
    leave_times = get_leave_time(chart, DEFAULT_CONFIG)
    assert leave_times == [
        LeaveTime(
            includes_break=True,
            min_time=Duration.parse("19:00"),
            wfh_cutoff_time=Duration.parse("12:00"),
        )
    ]


def test_leave_time_with_break_part_time():
    # With 6h/day, accumulated overtime from prior days is higher,
    # so required_today drops below 6h and no break is needed.
    chart = load_mock_attendance_chart("when_break.html")
    leave_times = get_leave_time(chart, PART_TIME_CONFIG)
    assert leave_times == [
        LeaveTime(includes_break=False, min_time=Duration.parse("13:31"))
    ]


def test_leave_time_no_break_part_time():
    chart = load_mock_attendance_chart("when_no_break.html")
    leave_times = get_leave_time(chart, PART_TIME_CONFIG)
    assert leave_times == [
        LeaveTime(includes_break=False, min_time=Duration.parse("09:39"))
    ]


def test_double_leave_time_part_time():
    # With 6h/day, enough prior overtime that required_today is well under 5h,
    # so a single no-break window is sufficient.
    chart = load_mock_attendance_chart("when_double_leave.html")
    leave_times = get_leave_time(chart, PART_TIME_CONFIG)
    assert leave_times == [
        LeaveTime(includes_break=False, min_time=Duration.parse("10:22"))
    ]
