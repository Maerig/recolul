import argparse
import sys
from getpass import getpass

from recolul import plotting, time
from recolul.config import Config
from recolul.duration import Duration
from recolul.recoru import AttendanceChart, RecoruSession
from recolul.time import get_today_hours


def balance(exclude_last_day: bool) -> None:
    attendance_chart = _get_attendance_chart()
    month = attendance_chart[:-1] if exclude_last_day else attendance_chart
    print(f"Monthly overtime balance: {time.get_overtime_balance(month)}")

    if exclude_last_day:
        return

    last_day = attendance_chart[-1]
    working_hours, break_time = get_today_hours(attendance_chart)
    print(f"\nLast day {last_day[0].text}")
    print(f"  Clock-in: {last_day[3].text}")
    print(f"  Working hours: {working_hours}")
    print(f"  Break: {break_time}")


def when_to_leave() -> None:
    attendance_chart = _get_attendance_chart()
    leave_time, includes_break = time.get_leave_time(attendance_chart)
    current_time = Duration.now()
    if leave_time <= current_time:
        print("Leave today as early as you like.")
        return

    break_msg = "(includes a 1-hour break)" if includes_break else "(break time not included)"
    print(f"Leave today at {leave_time} to avoid overtime {break_msg}.")


def update_config() -> None:
    """Needs to match Config.load"""
    recoru_contract_id = input("recoru.contractId: ")
    recoru_auth_id = input("recoru.authId: ")
    recoru_password = getpass("recoru.password: ")
    config = Config(
        recoru_contract_id=recoru_contract_id,
        recoru_auth_id=recoru_auth_id,
        recoru_password=recoru_password
    )
    config.save()


def graph(exclude_last_day: bool) -> None:
    attendance_chart = _get_attendance_chart()
    if exclude_last_day and len(attendance_chart) > 1:
        attendance_chart = attendance_chart[:-1]
    days, history = time.get_overtime_history(attendance_chart)
    plotting.plot_overtime_balance_history(days, history)


def main() -> None:
    parser = argparse.ArgumentParser(prog="recolul")
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
    match args.command:
        case "balance":
            balance(exclude_last_day=args.exclude_last_day)
        case "when":
            when_to_leave()
        case "config":
            update_config()
        case "graph":
            graph(exclude_last_day=args.exclude_last_day)


def _get_attendance_chart() -> AttendanceChart:
    config = Config.from_env() or Config.load()
    if not config:
        raise RuntimeError(f"No config found")

    with RecoruSession(
        contract_id=config.recoru_contract_id,
        auth_id=config.recoru_auth_id,
        password=config.recoru_password
    ) as recoru_session:
        attendance_chart = recoru_session.get_attendance_chart()
        # Remove rows without a clock-in time
        attendance_chart = [
            row for row in attendance_chart
            if row[3].text
        ]
        return attendance_chart


if __name__ == "__main__":
    main()
