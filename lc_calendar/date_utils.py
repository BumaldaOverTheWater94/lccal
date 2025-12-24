from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .config import CST_TZ


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
