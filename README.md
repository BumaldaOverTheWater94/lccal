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

### Record a new problem

```bash
lccal prob <problem_number>
lccal prob <problem_number> -e  # Extended mode
```

Records a problem attempted today. Creates revisit dates:

**Standard mode (default):**
- Revisit #1: 3 days later
- Revisit #2: 14 days later (2 weeks)
- Revisit #3: 30 days later (1 month)

**Extended mode (`-e` or `--extended`):**
- Revisit #1-3: Same as standard
- Revisit #4: 3 months later
- Revisit #5: 6 months later
- Revisit #6: 1 year later

### Backfill a past problem

```bash
lccal backfill <date> <problem_number>
lccal backfill <date> <problem_number> -e  # Extended mode
```

Records a problem from a past date. Date format: `MM/DD/YYYY`

Example: `lccal backfill 12/20/2025 123 -e`

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
