import math
import statistics
from datetime import timedelta
import plotly.graph_objects as go
from .config import Colors
from .storage import load_data, save_data
from .date_utils import (
    get_today,
    parse_date,
    format_date,
    calculate_revisit_dates,
    calculate_original_date,
)
from .core import add_problem_to_dates


def cmd_today():
    data = load_data()
    today = get_today()
    today_str = format_date(today)

    print(f"{Colors.BOLD}{Colors.CYAN}Today: {today_str}{Colors.RESET}")
    print()

    # Find problems with recent completions (within 1 day grace period)
    problems_in_grace_period = set()
    for date_str, problems in data["dates"].items():
        for problem in problems:
            if problem.get("completed") and "completed_date" in problem:
                completed_date = parse_date(problem["completed_date"])
                days_since_completion = (today - completed_date).days
                if days_since_completion < 1:
                    problems_in_grace_period.add(problem["number"])

    # Collect all pending problems with their dates
    all_pending = []
    for date_str, problems in data["dates"].items():
        date = parse_date(date_str)
        for problem in problems:
            if "completed" not in problem:
                problem["completed"] = False
            if not problem["completed"] and date <= today:
                # Exclude problems in grace period
                if problem["number"] not in problems_in_grace_period:
                    all_pending.append((date, date_str, problem))

    # Group by problem number and keep only the oldest revisit
    oldest_revisits = {}
    for date, date_str, problem in all_pending:
        problem_num = problem["number"]
        if problem_num not in oldest_revisits or date < oldest_revisits[problem_num][0]:
            oldest_revisits[problem_num] = (date, date_str, problem)

    # Separate into today and past
    today_problems = []
    past_problems = []
    for date, date_str, problem in oldest_revisits.values():
        if date == today:
            today_problems.append(problem)
        else:
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
    oldest_problem["completed_date"] = format_date(today)
    save_data(data)

    print(
        f"{Colors.GREEN}Problem {Colors.BOLD}{problem_number}{Colors.RESET}{Colors.GREEN} marked as done for {oldest_date_str} (Revisit #{oldest_problem['revisit']}){Colors.RESET}"
    )


def cmd_stats(start_date_str=None):
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

    if start_date_str:
        first_date = parse_date(start_date_str)
    else:
        first_date = min(parse_date(date_str) for date_str in problems_per_day.keys())
    
    last_date = get_today()

    complete_problems_per_day = {}
    current_date = first_date
    while current_date <= last_date:
        date_str = format_date(current_date)
        complete_problems_per_day[date_str] = problems_per_day.get(date_str, 0)
        current_date += timedelta(days=1)

    total_problems = len(problem_first_revisits)
    daily_counts = list(complete_problems_per_day.values())

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

    sorted_dates = sorted(complete_problems_per_day.keys(), key=parse_date)
    sorted_counts = [complete_problems_per_day[date] for date in sorted_dates]

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
        title="New Problems Attempted Per Day",
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
