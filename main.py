import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from dateutil import tz


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
    return datetime.strptime(date_str, "%m/%d/%Y").date()


def format_date(date):
    return date.strftime("%m/%d/%Y")


def calculate_revisit_dates(initial_date):
    return [
        initial_date + timedelta(days=3),
        initial_date + timedelta(days=14),
        initial_date + timedelta(days=30),
    ]


def add_problem_to_dates(data, problem_number, initial_date):
    revisit_dates = calculate_revisit_dates(initial_date)

    for i, revisit_date in enumerate(revisit_dates, 1):
        date_str = format_date(revisit_date)
        if date_str not in data["dates"]:
            data["dates"][date_str] = []
        data["dates"][date_str].append({
            "number": problem_number,
            "revisit": i,
            "completed": False
        })


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
        for date_str, problem in sorted(past_problems, key=lambda x: (parse_date(x[0]), x[1]["number"])):
            print(f"  - Problem {problem['number']} (Revisit #{problem['revisit']}) - Due: {date_str}")

    if not today_problems and not past_problems:
        print("No problems to revisit today.")


def cmd_prob(problem_number):
    data = load_data()
    today = get_today()
    today_str = format_date(today)

    add_problem_to_dates(data, problem_number, today)
    save_data(data)

    revisit_dates = calculate_revisit_dates(today)
    print(f"Problem {problem_number} recorded for {today_str}")
    print(f"Revisit dates:")
    print(f"  - Revisit #1: {format_date(revisit_dates[0])}")
    print(f"  - Revisit #2: {format_date(revisit_dates[1])}")
    print(f"  - Revisit #3: {format_date(revisit_dates[2])}")


def cmd_backfill(date_str, problem_number):
    data = load_data()

    try:
        initial_date = parse_date(date_str)
    except ValueError:
        print(f"Error: Invalid date format. Use MM/DD/YYYY")
        return

    add_problem_to_dates(data, problem_number, initial_date)
    save_data(data)

    revisit_dates = calculate_revisit_dates(initial_date)
    print(f"Problem {problem_number} backfilled for {date_str}")
    print(f"Revisit dates:")
    print(f"  - Revisit #1: {format_date(revisit_dates[0])}")
    print(f"  - Revisit #2: {format_date(revisit_dates[1])}")
    print(f"  - Revisit #3: {format_date(revisit_dates[2])}")


def cmd_del(problem_number):
    data = load_data()
    removed_count = 0

    for date_str in list(data["dates"].keys()):
        original_len = len(data["dates"][date_str])
        data["dates"][date_str] = [p for p in data["dates"][date_str] if p["number"] != problem_number]
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
        print(f"Problem {problem_number} is already marked as done for {oldest_date_str}")
        return

    oldest_problem["completed"] = True
    save_data(data)

    print(f"Problem {problem_number} marked as done for {oldest_date_str} (Revisit #{oldest_problem['revisit']})")


def main():
    parser = argparse.ArgumentParser(description="LC Calendar - Track LeetCode problem revisits")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("today", help="Show problems to revisit today")

    prob_parser = subparsers.add_parser("prob", help="Record a problem attempted today")
    prob_parser.add_argument("number", type=int, help="LeetCode problem number")

    backfill_parser = subparsers.add_parser("backfill", help="Record a problem from a past date")
    backfill_parser.add_argument("date", help="Date in MM/DD/YYYY format")
    backfill_parser.add_argument("number", type=int, help="LeetCode problem number")

    del_parser = subparsers.add_parser("del", help="Delete a problem and all its revisits")
    del_parser.add_argument("number", type=int, help="LeetCode problem number")

    done_parser = subparsers.add_parser("done", help="Mark a problem as completed")
    done_parser.add_argument("number", type=int, help="LeetCode problem number")

    args = parser.parse_args()

    if args.command == "today":
        cmd_today()
    elif args.command == "prob":
        cmd_prob(args.number)
    elif args.command == "backfill":
        cmd_backfill(args.date, args.number)
    elif args.command == "del":
        cmd_del(args.number)
    elif args.command == "done":
        cmd_done(args.number)


if __name__ == "__main__":
    main()
