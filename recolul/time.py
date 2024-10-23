import dataclasses
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
    if category.endswith(("Leave", "Leagve")) or category == "Flexible Holiday":
        return Duration(8 * 60)

    if not (raw_clock_in_time := entry.clock_in_time):
        return Duration(0)
    clock_in_time = Duration.parse(raw_clock_in_time)

    if raw_clock_out_time := entry.clock_out_time:
        clock_out_time = Duration.parse(raw_clock_out_time)
    else:
        # Current day
        clock_out_time = Duration.now()

    if clock_out_time < clock_in_time:
        # After midnight
        clock_out_time += Duration(24 * 60)

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

        row_work_time = Duration()
        for entry in row.entries:
            entry_work_time = get_entry_work_time(entry)
            row_work_time += entry_work_time

            workplace = entry.workplace or "HF Bldg."  # Workplace is empty for paid leaves
            total_workplace_times[workplace] += entry_work_time

        if not (required_time or row_work_time):
            # Can have work time during holidays
            continue

        days.append(day)
        overtime_history.append(row_work_time - required_time)

    return days, overtime_history, total_workplace_times


def get_overtime_balance(attendance_chart: AttendanceChart) -> tuple[Duration, dict[str, Duration]]:
    _, history, total_workplace_times = get_overtime_history(attendance_chart)
    return sum(history, Duration()), total_workplace_times


@dataclasses.dataclass
class LeaveTime:
    includes_break: bool
    min_time: Duration
    max_time: Duration | None = None


def get_leave_time(attendance_chart: AttendanceChart) -> list[LeaveTime]:
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

    required_today = day_base_hours - overtime_balance
    leave_time_without_break = last_clock_in + required_today
    leave_time_with_break = last_clock_in + required_today + Duration(60)
    if required_today > _MIN_HOURS_FOR_MANDATORY_BREAK:
        # When more than 6 hours must be achieved during the day,
        # add a mandatory 1-hour break time.
        return [
            LeaveTime(includes_break=True, min_time=leave_time_with_break)
        ]
    if required_today > _MIN_HOURS_FOR_MANDATORY_BREAK - Duration(60):
        # When the required time is between 5 and 6 hours, there is a first interval where
        # the overtime balance becomes positive, and then it becomes negative again when 6
        # hours have been worked because an hour is subtracted for break time.
        first_leave_time = LeaveTime(
            includes_break=False,
            min_time=leave_time_without_break,
            max_time=last_clock_in + _MIN_HOURS_FOR_MANDATORY_BREAK
        )
        second_leave_time = LeaveTime(includes_break=True, min_time=leave_time_with_break)
        return [first_leave_time, second_leave_time]
    return [
            LeaveTime(includes_break=False, min_time=leave_time_without_break)
        ]


def count_working_days(attendance_chart: AttendanceChart) -> int:
    return sum(
        1
        for row in attendance_chart
        if _is_working_day(row)
    )


def _is_working_day(row: ChartRow) -> bool:
    return row.day.text and row.day.color not in ["blue", "red"] or "swap day" in row.memo.lower()
