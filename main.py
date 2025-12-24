import argparse
import json
import math
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from dateutil import tz
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go


DATA_FILE = Path.home() / ".lccal_data.json"
CST_TZ = tz.gettz("America/Chicago")


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


def load_data():
    if not DATA_FILE.exists():
        return {"dates": {}}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_today():
    return datetime.now(CST_TZ).date()


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%m/%d/%Y").date()
    except ValueError:
        return datetime.strptime(date_str, "%m/%d/%y").date()


def format_date(date):
    return date.strftime("%m/%d/%Y")


def calculate_revisit_dates(initial_date, extended=False):
    dates = [
        initial_date + timedelta(days=3),
        initial_date + timedelta(days=14),
        initial_date + timedelta(days=30),
    ]
    if extended:
        dates.extend(
            [
                initial_date + relativedelta(months=3),
                initial_date + relativedelta(months=6),
                initial_date + relativedelta(years=1),
            ]
        )
    return dates


def calculate_original_date(revisit_date, revisit_number):
    if revisit_number == 1:
        return revisit_date - timedelta(days=3)
    elif revisit_number == 2:
        return revisit_date - timedelta(days=14)
    elif revisit_number == 3:
        return revisit_date - timedelta(days=30)
    elif revisit_number == 4:
        return revisit_date - relativedelta(months=3)
    elif revisit_number == 5:
        return revisit_date - relativedelta(months=6)
    elif revisit_number == 6:
        return revisit_date - relativedelta(years=1)
    else:
        return revisit_date


def add_problem_to_dates(data, problem_number, initial_date, extended=False):
    revisit_dates = calculate_revisit_dates(initial_date, extended)

    for i, revisit_date in enumerate(revisit_dates, 1):
        date_str = format_date(revisit_date)
        if date_str not in data["dates"]:
            data["dates"][date_str] = []
        data["dates"][date_str].append(
            {"number": problem_number, "revisit": i, "completed": False}
        )


def cmd_today():
    data = load_data()
    today = get_today()
    today_str = format_date(today)

    print(f"{Colors.BOLD}{Colors.CYAN}Today: {today_str}{Colors.RESET}")
    print()

    today_problems = []
    past_problems = []

    for date_str, problems in data["dates"].items():
        date = parse_date(date_str)
        for problem in problems:
            if "completed" not in problem:
                problem["completed"] = False
            if not problem["completed"]:
                if date == today:
                    today_problems.append(problem)
                elif date < today:
                    past_problems.append((date_str, problem))

    if today_problems:
        print(f"{Colors.BOLD}{Colors.GREEN}Problems to revisit today:{Colors.RESET}")
        for problem in sorted(today_problems, key=lambda x: x["number"]):
            print(
                f"{Colors.GREEN}  - Problem {Colors.BOLD}{problem['number']}{Colors.RESET}{Colors.GREEN} (Revisit #{problem['revisit']}){Colors.RESET}"
            )

    if past_problems:
        print()
        print(f"{Colors.BOLD}{Colors.RED}Past pending problems:{Colors.RESET}")
        for date_str, problem in sorted(
            past_problems, key=lambda x: (parse_date(x[0]), x[1]["number"])
        ):
            print(
                f"{Colors.YELLOW}  - Problem {Colors.BOLD}{problem['number']}{Colors.RESET}{Colors.YELLOW} (Revisit #{problem['revisit']}) - Due: {date_str}{Colors.RESET}"
            )

    if not today_problems and not past_problems:
        print(f"{Colors.BLUE}No problems to revisit today.{Colors.RESET}")


def cmd_add(problem_number, date_str=None, extended=False):
    data = load_data()

    if date_str:
        try:
            initial_date = parse_date(date_str)
        except ValueError:
            print(
                f"{Colors.RED}Error: Invalid date format. Use MM/DD/YYYY or MM/DD/YY{Colors.RESET}"
            )
            return
    else:
        initial_date = get_today()
        date_str = format_date(initial_date)

    add_problem_to_dates(data, problem_number, initial_date, extended)
    save_data(data)

    revisit_dates = calculate_revisit_dates(initial_date, extended)
    print(
        f"{Colors.GREEN}Problem {Colors.BOLD}{problem_number}{Colors.RESET}{Colors.GREEN} recorded for {date_str}{Colors.RESET}"
    )
    print(f"{Colors.CYAN}Revisit dates:{Colors.RESET}")
    for i, date in enumerate(revisit_dates, 1):
        print(f"{Colors.BLUE}  - Revisit #{i}: {format_date(date)}{Colors.RESET}")


def cmd_del(problem_number):
    data = load_data()
    removed_count = 0

    for date_str in list(data["dates"].keys()):
        original_len = len(data["dates"][date_str])
        data["dates"][date_str] = [
            p for p in data["dates"][date_str] if p["number"] != problem_number
        ]
        removed_count += original_len - len(data["dates"][date_str])

        if not data["dates"][date_str]:
            del data["dates"][date_str]

    save_data(data)

    if removed_count > 0:
        print(
            f"{Colors.GREEN}Problem {Colors.BOLD}{problem_number}{Colors.RESET}{Colors.GREEN} removed ({removed_count} revisit(s) deleted){Colors.RESET}"
        )
    else:
        print(f"{Colors.RED}Problem {problem_number} not found{Colors.RESET}")


def cmd_done(problem_number):
    data = load_data()
    today = get_today()

    candidates = []
    for date_str, problems in data["dates"].items():
        date = parse_date(date_str)
        if date <= today:
            for problem in problems:
                if problem["number"] == problem_number:
                    if "completed" not in problem:
                        problem["completed"] = False
                    candidates.append((date, date_str, problem))

    if not candidates:
        print(f"{Colors.RED}Problem {problem_number} not found{Colors.RESET}")
        return

    candidates.sort(key=lambda x: x[0])
    oldest_date, oldest_date_str, oldest_problem = candidates[0]

    if oldest_problem["completed"]:
        print(
            f"{Colors.YELLOW}Problem {problem_number} is already marked as done for {oldest_date_str}{Colors.RESET}"
        )
        return

    oldest_problem["completed"] = True
    save_data(data)

    print(
        f"{Colors.GREEN}Problem {Colors.BOLD}{problem_number}{Colors.RESET}{Colors.GREEN} marked as done for {oldest_date_str} (Revisit #{oldest_problem['revisit']}){Colors.RESET}"
    )


def cmd_stats():
    data = load_data()

    if not data["dates"]:
        print(f"{Colors.YELLOW}No data available for statistics.{Colors.RESET}")
        return

    problem_first_revisits = {}

    for date_str, problems in data["dates"].items():
        date = parse_date(date_str)
        for problem in problems:
            problem_num = problem["number"]
            revisit_num = problem["revisit"]

            if problem_num not in problem_first_revisits:
                problem_first_revisits[problem_num] = (date, revisit_num)
            else:
                existing_date, existing_revisit = problem_first_revisits[problem_num]
                if revisit_num < existing_revisit:
                    problem_first_revisits[problem_num] = (date, revisit_num)

    problems_per_day = {}

    for problem_num, (revisit_date, revisit_num) in problem_first_revisits.items():
        original_date = calculate_original_date(revisit_date, revisit_num)
        date_str = format_date(original_date)

        if date_str not in problems_per_day:
            problems_per_day[date_str] = 0
        problems_per_day[date_str] += 1

    if not problems_per_day:
        print(f"{Colors.YELLOW}No problems found for statistics.{Colors.RESET}")
        return

    total_problems = len(problem_first_revisits)
    daily_counts = list(problems_per_day.values())

    mean_per_day = statistics.mean(daily_counts)
    median_per_day = statistics.median(daily_counts)

    if len(daily_counts) > 1:
        std_dev_per_day = statistics.stdev(daily_counts)
    else:
        std_dev_per_day = 0.0

    range_per_day = max(daily_counts) - min(daily_counts)

    try:
        mode_per_day = statistics.mode(daily_counts)
    except statistics.StatisticsError:
        mode_per_day = None

    sorted_dates = sorted(problems_per_day.keys(), key=parse_date)
    sorted_counts = [problems_per_day[date] for date in sorted_dates]

    max_count = max(sorted_counts)
    y_upper = (math.floor(max_count / 10) + 1) * 10

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=sorted_dates,
            y=sorted_counts,
            mode="lines+markers",
            name="Problems per day",
            line=dict(color="blue", width=2),
            marker=dict(size=6),
        )
    )

    fig.add_hline(
        y=mean_per_day,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Mean: {mean_per_day:.2f}",
        annotation_position="right",
    )

    fig.add_hline(
        y=median_per_day,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Median: {median_per_day:.2f}",
        annotation_position="right",
    )

    fig.update_layout(
        title="LeetCode Problems Attempted Per Day",
        xaxis_title="Date",
        yaxis_title="Number of Problems",
        yaxis=dict(range=[0, y_upper]),
        hovermode="x unified",
        template="plotly_white",
    )

    fig.show()

    print(f"\n{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}LeetCode Problem Statistics{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}\n")
    print(
        f"{Colors.GREEN}Total problems attempted: {Colors.BOLD}{total_problems}{Colors.RESET}"
    )
    print(f"\n{Colors.CYAN}Problems per day statistics:{Colors.RESET}")
    print(f"{Colors.BLUE}  Mean:       {Colors.BOLD}{mean_per_day:.2f}{Colors.RESET}")
    print(f"{Colors.BLUE}  Median:     {Colors.BOLD}{median_per_day:.2f}{Colors.RESET}")
    print(
        f"{Colors.BLUE}  Std Dev:    {Colors.BOLD}{std_dev_per_day:.2f}{Colors.RESET}"
    )
    print(f"{Colors.BLUE}  Range:      {Colors.BOLD}{range_per_day}{Colors.RESET}")
    if mode_per_day is not None:
        print(f"{Colors.BLUE}  Mode:       {Colors.BOLD}{mode_per_day}{Colors.RESET}")
    else:
        print(f"{Colors.BLUE}  Mode:       {Colors.YELLOW}N/A (no mode){Colors.RESET}")
    print(f"\n{Colors.CYAN}{'=' * 50}{Colors.RESET}\n")


def main():
    parser = argparse.ArgumentParser(
        description="LC Calendar - Track LeetCode problem revisits"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("today", help="Show problems to revisit today")

    add_parser = subparsers.add_parser("add", help="Add a problem (today or backfill)")
    add_parser.add_argument("number", type=int, help="LeetCode problem number")
    add_parser.add_argument(
        "date",
        nargs="?",
        help="Optional date in MM/DD/YYYY or MM/DD/YY format (defaults to today)",
    )
    add_parser.add_argument(
        "-e",
        "--extended",
        action="store_true",
        help="Use extended revisit pattern (3mo, 6mo, 1yr)",
    )

    del_parser = subparsers.add_parser(
        "del", help="Delete a problem and all its revisits"
    )
    del_parser.add_argument("number", type=int, help="LeetCode problem number")

    done_parser = subparsers.add_parser("done", help="Mark a problem as completed")
    done_parser.add_argument("number", type=int, help="LeetCode problem number")

    subparsers.add_parser("stats", help="Show problem statistics and graph")

    args = parser.parse_args()

    if args.command == "today":
        cmd_today()
    elif args.command == "add":
        cmd_add(args.number, args.date, args.extended)
    elif args.command == "del":
        cmd_del(args.number)
    elif args.command == "done":
        cmd_done(args.number)
    elif args.command == "stats":
        cmd_stats()


if __name__ == "__main__":
    main()
