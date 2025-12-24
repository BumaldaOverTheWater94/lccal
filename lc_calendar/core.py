from .date_utils import calculate_revisit_dates, format_date


def add_problem_to_dates(data, problem_number, initial_date, extended=False):
    revisit_dates = calculate_revisit_dates(initial_date, extended)

    for i, revisit_date in enumerate(revisit_dates, 1):
        date_str = format_date(revisit_date)
        if date_str not in data["dates"]:
            data["dates"][date_str] = []
        data["dates"][date_str].append(
            {"number": problem_number, "revisit": i, "completed": False}
        )
