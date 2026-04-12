import argparse
import sys
from getpass import getpass

from recolul import __version__, plotting, time
from recolul.config import Config, DEFAULT_HOURS_PER_DAY, DEFAULT_WFH_HOURS_PER_DAY
from recolul.errors import NoClockInError
from recolul.recoru.attendance_chart import AttendanceChart
from recolul.recoru.recoru_session import RecoruSession
from recolul.time import get_max_wfh_time, get_row_work_time, until_today


def balance(config: Config, exclude_last_day: bool) -> None:
    full_attendance_chart = _get_attendance_chart(config)
    attendance_chart = until_today(full_attendance_chart)
    if exclude_last_day and len(attendance_chart) > 1:
        attendance_chart = attendance_chart[:-1]
    overtime_balance, total_workplace_times = time.get_overtime_balance(attendance_chart, config)
    print(f"Monthly overtime balance: {overtime_balance}")
    print(f"Total time per workplace:")
    for workplace, total_work_time in total_workplace_times.items():
        print(f"  {workplace}: {total_work_time}")
    print(f"Maximum WFH time this month: {get_max_wfh_time(full_attendance_chart, config)}")

    if exclude_last_day:
        return

    last_day = attendance_chart[-1]
    print(f"\nLast day {last_day.day.text}")
    print(f"  Clock-in: {max(entry.clock_in_time for entry in last_day.entries)}")
    print(f"  Working hours: {get_row_work_time(last_day, config)}")


def when_to_leave(config: Config) -> None:
    try:
        full_attendance_chart = _get_attendance_chart(config)
        leave_times = time.get_leave_time(full_attendance_chart, config)
    except NoClockInError:
        print("You have already clocked out.")
        return

    if len(leave_times) == 1:
        break_msg = "(break time included)" if leave_times[0].includes_break else "(break time not included)"
        print(f"Leave at {leave_times[0].min_time} to avoid overtime {break_msg}.")
    else:
        print(
            f"Leave between {leave_times[0].min_time} and {leave_times[0].max_time}, or """
            f"after {leave_times[1].min_time}."
        )

    for lt in leave_times:
        if not lt.wfh_cutoff_time:
            continue
        break_msg = "(break time included)" if lt.wfh_cutoff_includes_break else "(break time not included)"
        print(f"Warning! Reaching maximum monthly WFH hours at {lt.wfh_cutoff_time} {break_msg}.")
        break


def update_config() -> None:
    """Needs to match Config.load"""
    recoru_contract_id = input("recoru.contractId: ")
    recoru_auth_id = input("recoru.authId: ")
    recoru_password = getpass("recoru.password: ")
    hours_per_day = input(f"recoru.hoursPerDay [{DEFAULT_HOURS_PER_DAY}]: ") or str(DEFAULT_HOURS_PER_DAY)
    wfh_hours_per_day = input(f"recoru.wfhHoursPerDay [{DEFAULT_WFH_HOURS_PER_DAY}]: ") or str(DEFAULT_WFH_HOURS_PER_DAY)
    config = Config(
        recoru_contract_id=recoru_contract_id,
        recoru_auth_id=recoru_auth_id,
        recoru_password=recoru_password,
        hours_per_day=int(hours_per_day),
        wfh_hours_per_day=float(wfh_hours_per_day),
    )
    config.save()


def graph(config: Config, exclude_last_day: bool) -> None:
    attendance_chart = until_today(_get_attendance_chart(config))
    if exclude_last_day and len(attendance_chart) > 1:
        attendance_chart = attendance_chart[:-1]
    days, history, _ = time.get_overtime_history(attendance_chart, config)
    plotting.plot_overtime_balance_history(days, history)


def main() -> None:
    parser = argparse.ArgumentParser(prog="recolul")
    parser.add_argument("-v", "--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    balance_parser = subparsers.add_parser("balance", help="Calculate overtime balance")
    balance_parser.add_argument(
        "--exclude-last-day",
        action="store_true",
        help="Exclude last/current day from the calculation"
    )

    subparsers.add_parser("when", help="Calculate at which time to leave to avoid overtime this month")

    subparsers.add_parser("config", help="Init or update config")

    graph_parser = subparsers.add_parser("graph", help="Display a graph of overtime balance over the month")
    graph_parser.add_argument(
        "--exclude-last-day",
        action="store_true",
        help="Exclude last/current day from the graph"
    )

    args = parser.parse_args(sys.argv[1:])
    if args.command == "config":
        update_config()
        return

    config = Config.from_env() or Config.load()
    if not config:
        raise RuntimeError("No config found")

    match args.command:
        case "balance":
            balance(config, exclude_last_day=args.exclude_last_day)
        case "when":
            when_to_leave(config)
        case "graph":
            graph(config, exclude_last_day=args.exclude_last_day)


def _get_attendance_chart(config: Config) -> AttendanceChart:
    with RecoruSession(
        contract_id=config.recoru_contract_id,
        auth_id=config.recoru_auth_id,
        password=config.recoru_password
    ) as recoru_session:
        attendance_chart = recoru_session.get_attendance_chart()

    return attendance_chart


if __name__ == "__main__":
    main()
