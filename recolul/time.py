from collections import defaultdict
from datetime import datetime

from recolul.duration import Duration
from recolul.errors import NoClockInError
from recolul.recoru.attendance_chart import AttendanceChart, ChartRow, ChartRowEntry

_MIN_HOURS_FOR_MANDATORY_BREAK = Duration(6 * 60)


def until_today(attendance_chart: AttendanceChart) -> AttendanceChart:
    """Return a slice of the attendance chart that only contains rows until today"""
    current_day_of_month = datetime.now().day
    return [
        row for row in attendance_chart
        if row.day_of_month <= current_day_of_month
    ]


def get_entry_work_time(entry: ChartRowEntry) -> Duration:
    """
    Get work time from the column if available,
    else calculate it from clock-in time and current time
    """
    category = entry.category
    if category.startswith("Half Day Leave"):
        return Duration(4 * 60)
    if category.endswith(("Leave", "Leagve")):
        return Duration(8 * 60)

    if not (raw_clock_in_time := entry.clock_in_time):
        return Duration(0)
    clock_in_time = Duration.parse(raw_clock_in_time)

    if raw_clock_out_time := entry.clock_out_time:
        clock_out_time = Duration.parse(raw_clock_out_time)
    else:
        # Current day
        clock_out_time = Duration.now()

    work_time = clock_out_time - clock_in_time
    break_time = (
        Duration(60) if work_time >= _MIN_HOURS_FOR_MANDATORY_BREAK
        else Duration(0)
    )
    return work_time - break_time


def get_row_work_time(row: ChartRow) -> Duration:
    total_work_time = Duration()
    for entry in row.entries:
        total_work_time += get_entry_work_time(entry)
    return total_work_time


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
        if not required_time:
            continue

        row_work_time = Duration()
        for entry in row.entries:
            entry_work_time = get_entry_work_time(entry)
            row_work_time += entry_work_time

            workplace = entry.workplace or "HF Bldg."  # Workplace is empty for paid leaves
            total_workplace_times[workplace] += entry_work_time

        days.append(day)
        overtime_history.append(row_work_time - required_time)

    return days, overtime_history, total_workplace_times


def get_overtime_balance(attendance_chart: AttendanceChart) -> tuple[Duration, dict[str, Duration]]:
    _, history, total_workplace_times = get_overtime_history(attendance_chart)
    return sum(history, Duration()), total_workplace_times


def get_leave_time(attendance_chart: AttendanceChart) -> tuple[Duration, bool]:
    day_base_hours = Duration(8 * 60)
    overtime_balance, _ = get_overtime_balance(attendance_chart[:-1])

    last_row = attendance_chart[-1]
    last_clock_in = None
    for entry in last_row.entries:
        if entry.clock_in_time and not entry.clock_out_time:
            # In progress
            last_clock_in = Duration.parse(entry.clock_in_time)
        else:
            # Complete entry
            overtime_balance += get_entry_work_time(entry)
    if not last_clock_in:
        raise NoClockInError()

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
