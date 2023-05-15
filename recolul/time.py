from collections import defaultdict

from recolul.duration import Duration
from recolul.recoru.attendance_chart import AttendanceChart, ChartRow

_MIN_HOURS_FOR_MANDATORY_BREAK = Duration(6 * 60)


def get_work_time(chart_row: ChartRow) -> Duration:
    """
    Get work time from the column if available,
    else calculate it from clock-in time and current time
    """
    if work_time := chart_row.work_time:
        return Duration.parse(work_time)

    clock_in_time = Duration.parse(chart_row.clock_in_time)
    current_work_time = Duration.now() - clock_in_time
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
        if not row.clock_in_time:
            continue

        day = row.day
        if not day.text:
            continue

        days.append(day.text)
        if day.color in ["blue", "red"] and "swap day" not in row.memo.lower():
            required_time = Duration(0)
        else:
            required_time = Duration(8 * 60)
        work_time = get_work_time(row)
        overtime_history.append(work_time - required_time)
        total_workplace_times[row.workplace.text] += work_time

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
