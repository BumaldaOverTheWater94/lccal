import argparse
from .commands import cmd_today, cmd_add, cmd_del, cmd_done, cmd_stats


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

    stats_parser = subparsers.add_parser("stats", help="Show problem statistics and graph")
    stats_parser.add_argument(
        "start_date",
        nargs="?",
        help="Optional start date in MM/DD/YYYY or MM/DD/YY format (defaults to first recorded day)",
    )

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
        cmd_stats(args.start_date)


if __name__ == "__main__":
    main()
