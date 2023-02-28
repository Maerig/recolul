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


def get_overtime_history(attendance_chart: AttendanceChart) -> tuple[list[str], list[Duration]]:
    days = []
    overtime_history = []
    for row in attendance_chart:
        if not row.clock_in_time:
            continue

        day = row.day
        if not day.text:
            continue

        days.append(day.text)
        required_time = Duration(0 if day.color in ["blue", "red"] else 8 * 60)  # No required hours for holidays
        work_time = get_work_time(row)
        overtime_history.append(work_time - required_time)

    return days, overtime_history


def get_overtime_balance(attendance_chart: AttendanceChart) -> Duration:
    _, history = get_overtime_history(attendance_chart)
    return sum(history, Duration())


def get_leave_time(attendance_chart: AttendanceChart) -> tuple[Duration, bool]:
    day_base_hours = Duration(8 * 60)
    overtime_balance = get_overtime_balance(attendance_chart[:-1])
    last_clock_in = Duration.parse(attendance_chart[-1].clock_in_time)

    leave_time = last_clock_in + day_base_hours - overtime_balance

    # When more than 6 hours must be achieved during the day,
    # add a mandatory 1-hour break time.
    required_today = day_base_hours - overtime_balance
    if required_today > _MIN_HOURS_FOR_MANDATORY_BREAK:
        leave_time += Duration(60)
        return leave_time, True

    return leave_time, False
