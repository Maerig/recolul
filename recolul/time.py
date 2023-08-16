from collections import defaultdict
from datetime import datetime

from recolul.duration import Duration
from recolul.recoru.attendance_chart import AttendanceChart, ChartRow

_MIN_HOURS_FOR_MANDATORY_BREAK = Duration(6 * 60)


def until_today(attendance_chart: AttendanceChart) -> AttendanceChart:
    """Return a slice of the attendance chart that only contains rows until today"""
    current_day_of_month = datetime.now().day
    return [
        row for row in attendance_chart
        if row.day_of_month <= current_day_of_month
    ]


def get_work_time(chart_row: ChartRow) -> Duration:
    """
    Get work time from the column if available,
    else calculate it from clock-in time and current time
    """
    if not chart_row.is_multiple_entry_row and (work_time := chart_row.work_time):
        return Duration.parse(work_time)

    category = chart_row.category
    if category.startswith("Half Day Leave"):
        return Duration(4 * 60)
    if category.endswith(("Leave", "Leagve")):
        return Duration(8 * 60)

    if not (raw_clock_in_time := chart_row.clock_in_time):
        return Duration(0)
    clock_in_time = Duration.parse(raw_clock_in_time)

    if raw_clock_out_time := chart_row.clock_out_time:
        clock_out_time = Duration.parse(raw_clock_out_time)
    else:
        # Current day
        clock_out_time = Duration.now()

    current_work_time = clock_out_time - clock_in_time
    break_time = (
        Duration(60) if current_work_time >= _MIN_HOURS_FOR_MANDATORY_BREAK
        else Duration(0)
    )
    return current_work_time - break_time


def get_overtime_history(attendance_chart: AttendanceChart) -> tuple[list[str], list[Duration], dict[str, Duration]]:
    days = []
    overtime_history = []
    total_workplace_times = defaultdict(Duration)
    for row in attendance_chart:
        day = row.day.text
        if not _is_working_day(row):
            required_time = Duration(0)
        else:
            required_time = Duration(8 * 60)
        work_time = get_work_time(row)
        if not (required_time or work_time):
            continue

        if day:
            days.append(day)
            overtime_history.append(work_time - required_time)
        else:
            # Row with multiple entries
            overtime_history[-1] += work_time

        workplace = row.workplace or "HF Bldg."  # Workplace is empty for paid leaves
        total_workplace_times[workplace] += work_time

    return days, overtime_history, total_workplace_times


def get_overtime_balance(attendance_chart: AttendanceChart) -> tuple[Duration, dict[str, Duration]]:
    _, history, total_workplace_times = get_overtime_history(attendance_chart)
    return sum(history, Duration()), total_workplace_times


def get_leave_time(attendance_chart: AttendanceChart) -> tuple[Duration, bool]:
    day_base_hours = Duration(8 * 60)
    overtime_balance, _ = get_overtime_balance(attendance_chart[:-1])
    last_clock_in = Duration.parse(attendance_chart[-1].clock_in_time)

    leave_time = last_clock_in + day_base_hours - overtime_balance

    # When more than 6 hours must be achieved during the day,
    # add a mandatory 1-hour break time.
    required_today = day_base_hours - overtime_balance
    if required_today > _MIN_HOURS_FOR_MANDATORY_BREAK:
        leave_time += Duration(60)
        return leave_time, True

    return leave_time, False


def count_working_days(attendance_chart: AttendanceChart) -> int:
    return sum(
        1
        for row in attendance_chart
        if _is_working_day(row)
    )


def _is_working_day(row: ChartRow) -> bool:
    return row.day.text and row.day.color not in ["blue", "red"] or "swap day" in row.memo.lower()
