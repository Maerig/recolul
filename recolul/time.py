from recolul.duration import Duration
from recolul.recoru import AttendanceChart, ChartRow

_MIN_HOURS_FOR_MANDATORY_BREAK = Duration(6 * 60)


def get_overtime_history(attendance_chart: AttendanceChart) -> tuple[list[str], list[Duration]]:
    days = []
    overtime_history = []
    for row in attendance_chart:
        if not row.clock_in_time:
            continue

        day = row.day
        days.append(day.text)
        working_hours, _ = get_hours(row)
        required_hours = Duration(0 if day.color in ["blue", "red"] else 8 * 60)  # No required hours for holidays
        overtime_history.append(working_hours - required_hours)

    return days, overtime_history


def get_overtime_balance(attendance_chart: AttendanceChart) -> Duration:
    _, history = get_overtime_history(attendance_chart)
    return sum(history, Duration())


def get_today_last_clock_in(attendance_chart: AttendanceChart) -> Duration:
    return Duration.parse(attendance_chart[-1].clock_in_time)


def get_hours(chart_row: ChartRow) -> tuple[Duration, Duration]:
    """Returns (working_hours, break_time)"""
    clock_in_time = Duration.parse(chart_row.clock_in_time)
    clock_out_time = (
        Duration.parse(clock_out_time) if (clock_out_time := chart_row.clock_out_time)
        else Duration.now()
    )
    total_time = clock_out_time - clock_in_time
    break_time = (
        Duration(60) if total_time >= _MIN_HOURS_FOR_MANDATORY_BREAK
        else Duration(0)
    )
    working_hours = total_time - break_time
    return working_hours, break_time


def get_today_hours(attendance_chart: AttendanceChart) -> tuple[Duration, Duration]:
    return get_hours(attendance_chart[-1])


def get_leave_time(attendance_chart: AttendanceChart) -> tuple[Duration, bool]:
    day_base_hours = Duration(8 * 60)
    overtime_balance = get_overtime_balance(attendance_chart[:-1])
    last_clock_in = get_today_last_clock_in(attendance_chart)
    _, today_break = get_today_hours(attendance_chart)

    leave_time = last_clock_in + day_base_hours - overtime_balance

    # When more than 6 hours must be achieved during the day,
    # add a mandatory 1-hour break time.
    required_today = day_base_hours - overtime_balance
    if (required_today > _MIN_HOURS_FOR_MANDATORY_BREAK) or (today_break > Duration(0)):
        leave_time += Duration(60)
        return leave_time, True

    return leave_time, False
