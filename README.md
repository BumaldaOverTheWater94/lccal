# LC Calendar

A CLI tool to track LeetCode problem revisits using spaced repetition.

## Installation

```bash
uv pip install -e .
```

## Usage

### View today's problems

```bash
lccal today
```

Shows problems due today and all past pending problems that haven't been completed.

### Add a problem

```bash
lccal add <problem_number>              # Add for today
lccal add <problem_number> <date>       # Backfill for past date
lccal add <problem_number> -e           # Extended mode (today)
lccal add <problem_number> <date> -e    # Extended mode (past date)
```

Records a problem and creates revisit dates. If no date is provided, uses today's date. Date format: `MM/DD/YYYY` or `MM/DD/YY`

**Standard mode (default):**
- Revisit #1: 3 days later
- Revisit #2: 14 days later (2 weeks)
- Revisit #3: 30 days later (1 month)

**Extended mode (`-e` or `--extended`):**
- Revisit #1-3: Same as standard
- Revisit #4: 3 months later
- Revisit #5: 6 months later
- Revisit #6: 1 year later

Examples:
- `lccal add 123` - Add problem 123 for today
- `lccal add 456 12/20/25` - Backfill problem 456 for 12/20/25
- `lccal add 789 -e` - Add problem 789 with extended pattern

### Mark problem as complete

```bash
lccal done <problem_number>
```

Marks the oldest pending revisit as completed.

Note: if you fail a retry, simply use `lccal del <problem_number>` then `lccal prob <problem_number>` to reset and shift the revisit pattern into the future starting from today's date

### Delete a problem

```bash
lccal del <problem_number>
```

Removes all revisits for a problem.

### View statistics

```bash
lccal stats
```

Displays statistics about your problem-solving habits including:
- Total problems attempted
- Mean, median, standard deviation, range, and mode of problems per day
- Interactive graph showing problems attempted per day over time

## Data Storage

Data is stored in `~/.lccal_data.json` with the following structure:

```json
{
  "dates": {
    "12/27/2025": [
      {
        "number": 123,
        "revisit": 1,
        "completed": false
      }
    ]
  }
}
```

## Timezone

All dates use CST (America/Chicago) timezone.

## Project Structure

The project is organized as a Python package with the following structure:

```
lc_calendar/
├── __init__.py          # Package exports
├── cli.py               # CLI entry point and argument parsing
├── config.py            # Configuration constants (DATA_FILE, CST_TZ, Colors)
├── storage.py           # Data persistence (load_data, save_data)
├── date_utils.py        # Date manipulation utilities
├── core.py              # Business logic (add_problem_to_dates)
└── commands.py          # Command handlers (cmd_today, cmd_add, cmd_del, cmd_done, cmd_stats)
```

This modular structure provides:
- **Clear separation of concerns**: Each module has a specific responsibility
- **Easy testing**: Individual modules can be tested in isolation
- **Maintainability**: Changes are localized to relevant modules
- **Extensibility**: New features can be added without modifying existing code
