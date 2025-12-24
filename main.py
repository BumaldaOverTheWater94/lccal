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

    print(f"Today: {today_str}")
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
        print("Problems to revisit today:")
        for problem in sorted(today_problems, key=lambda x: x["number"]):
            print(f"  - Problem {problem['number']} (Revisit #{problem['revisit']})")

    if past_problems:
        print()
        print("Past pending problems:")
        for date_str, problem in sorted(
            past_problems, key=lambda x: (parse_date(x[0]), x[1]["number"])
        ):
            print(
                f"  - Problem {problem['number']} (Revisit #{problem['revisit']}) - Due: {date_str}"
            )

    if not today_problems and not past_problems:
        print("No problems to revisit today.")


def cmd_add(problem_number, date_str=None, extended=False):
    data = load_data()

    if date_str:
        try:
            initial_date = parse_date(date_str)
        except ValueError:
            print(f"Error: Invalid date format. Use MM/DD/YYYY or MM/DD/YY")
            return
    else:
        initial_date = get_today()
        date_str = format_date(initial_date)

    add_problem_to_dates(data, problem_number, initial_date, extended)
    save_data(data)

    revisit_dates = calculate_revisit_dates(initial_date, extended)
    print(f"Problem {problem_number} recorded for {date_str}")
    print(f"Revisit dates:")
    for i, date in enumerate(revisit_dates, 1):
        print(f"  - Revisit #{i}: {format_date(date)}")


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
        print(f"Problem {problem_number} removed ({removed_count} revisit(s) deleted)")
    else:
        print(f"Problem {problem_number} not found")


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
        print(f"Problem {problem_number} not found")
        return

    candidates.sort(key=lambda x: x[0])
    oldest_date, oldest_date_str, oldest_problem = candidates[0]

    if oldest_problem["completed"]:
        print(
            f"Problem {problem_number} is already marked as done for {oldest_date_str}"
        )
        return

    oldest_problem["completed"] = True
    save_data(data)

    print(
        f"Problem {problem_number} marked as done for {oldest_date_str} (Revisit #{oldest_problem['revisit']})"
    )


def cmd_stats():
    data = load_data()
    
    if not data["dates"]:
        print("No data available for statistics.")
        return
    
    # Find original attempt dates for each problem
    problem_first_revisits = {}
    
    for date_str, problems in data["dates"].items():
        date = parse_date(date_str)
        for problem in problems:
            problem_num = problem["number"]
            revisit_num = problem["revisit"]
            
            if problem_num not in problem_first_revisits:
                problem_first_revisits[problem_num] = (date, revisit_num)
            else:
                # Keep the earliest revisit (lowest revisit number)
                existing_date, existing_revisit = problem_first_revisits[problem_num]
                if revisit_num < existing_revisit:
                    problem_first_revisits[problem_num] = (date, revisit_num)
    
    # Calculate original dates and count problems per day
    problems_per_day = {}
    
    for problem_num, (revisit_date, revisit_num) in problem_first_revisits.items():
        original_date = calculate_original_date(revisit_date, revisit_num)
        date_str = format_date(original_date)
        
        if date_str not in problems_per_day:
            problems_per_day[date_str] = 0
        problems_per_day[date_str] += 1
    
    if not problems_per_day:
        print("No problems found for statistics.")
        return
    
    # Calculate statistics
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
    
    # Sort dates chronologically for plotting
    sorted_dates = sorted(problems_per_day.keys(), key=parse_date)
    sorted_counts = [problems_per_day[date] for date in sorted_dates]

    # Calculate y-axis upper bound (round up to nearest 10)
    max_count = max(sorted_counts)
    y_upper = (math.floor(max_count / 10) + 1) * 10

    # Create plotly line graph
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sorted_dates,
        y=sorted_counts,
        mode='lines+markers',
        name='Problems per day',
        line=dict(color='blue', width=2),
        marker=dict(size=6)
    ))

    # Add mean line
    fig.add_hline(
        y=mean_per_day,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Mean: {mean_per_day:.2f}",
        annotation_position="right"
    )

    # Add median line
    fig.add_hline(
        y=median_per_day,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Median: {median_per_day:.2f}",
        annotation_position="right"
    )

    fig.update_layout(
        title='LeetCode Problems Attempted Per Day',
        xaxis_title='Date',
        yaxis_title='Number of Problems',
        yaxis=dict(range=[0, y_upper]),
        hovermode='x unified',
        template='plotly_white'
    )
    
    fig.show()
    
    # Print statistics
    print(f"\n{'='*50}")
    print("LeetCode Problem Statistics")
    print(f"{'='*50}\n")
    print(f"Total problems attempted: {total_problems}")
    print(f"\nProblems per day statistics:")
    print(f"  Mean:       {mean_per_day:.2f}")
    print(f"  Median:     {median_per_day:.2f}")
    print(f"  Std Dev:    {std_dev_per_day:.2f}")
    print(f"  Range:      {range_per_day}")
    if mode_per_day is not None:
        print(f"  Mode:       {mode_per_day}")
    else:
        print(f"  Mode:       N/A (no mode)")
    print(f"\n{'='*50}\n")


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
