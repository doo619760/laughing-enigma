"""Date utility functions for California court case tracking."""

from datetime import date, datetime, timedelta
from typing import Optional, List, Union


def parse_date(date_string: str) -> Optional[date]:
    """
    Parse a date string into a date object.

    Supports multiple formats:
    - MM/DD/YYYY
    - YYYY-MM-DD
    - MM-DD-YYYY
    - Month DD, YYYY
    """
    formats = [
        '%m/%d/%Y',
        '%Y-%m-%d',
        '%m-%d-%Y',
        '%B %d, %Y',
        '%b %d, %Y',
        '%m/%d/%y',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_string.strip(), fmt).date()
        except ValueError:
            continue

    return None


def format_date(d: date, format_style: str = 'standard') -> str:
    """
    Format a date for display.

    Styles:
    - standard: 01/15/2024
    - iso: 2024-01-15
    - long: January 15, 2024
    - short: Jan 15, 2024
    """
    formats = {
        'standard': '%m/%d/%Y',
        'iso': '%Y-%m-%d',
        'long': '%B %d, %Y',
        'short': '%b %d, %Y',
    }

    fmt = formats.get(format_style, '%m/%d/%Y')
    return d.strftime(fmt)


def days_between(start: date, end: date) -> int:
    """Calculate the number of days between two dates."""
    return (end - start).days


def days_until(target: date) -> int:
    """Calculate days until a target date from today."""
    return (target - date.today()).days


def days_since(past_date: date) -> int:
    """Calculate days since a past date from today."""
    return (date.today() - past_date).days


def is_business_day(check_date: date, holidays: Optional[List[date]] = None) -> bool:
    """
    Check if a date is a business day (Monday-Friday, not a holiday).

    Args:
        check_date: The date to check
        holidays: Optional list of holiday dates to exclude
    """
    # Check weekend
    if check_date.weekday() >= 5:
        return False

    # Check holidays
    if holidays and check_date in holidays:
        return False

    return True


def add_business_days(start_date: date, business_days: int,
                       holidays: Optional[List[date]] = None) -> date:
    """
    Add business days to a date.

    Skips weekends and optionally holidays.
    """
    result = start_date
    days_added = 0

    while days_added < business_days:
        result += timedelta(days=1)
        if is_business_day(result, holidays):
            days_added += 1

    return result


def subtract_business_days(end_date: date, business_days: int,
                            holidays: Optional[List[date]] = None) -> date:
    """
    Subtract business days from a date.

    Skips weekends and optionally holidays.
    """
    result = end_date
    days_subtracted = 0

    while days_subtracted < business_days:
        result -= timedelta(days=1)
        if is_business_day(result, holidays):
            days_subtracted += 1

    return result


def get_next_business_day(from_date: date,
                          holidays: Optional[List[date]] = None) -> date:
    """Get the next business day from a given date."""
    result = from_date
    while not is_business_day(result, holidays):
        result += timedelta(days=1)
    return result


def get_week_range(reference_date: Optional[date] = None) -> tuple:
    """Get the start and end dates of the week containing the reference date."""
    if reference_date is None:
        reference_date = date.today()

    start = reference_date - timedelta(days=reference_date.weekday())
    end = start + timedelta(days=6)
    return start, end


def get_month_range(reference_date: Optional[date] = None) -> tuple:
    """Get the start and end dates of the month containing the reference date."""
    if reference_date is None:
        reference_date = date.today()

    start = reference_date.replace(day=1)

    # Get last day of month
    if reference_date.month == 12:
        end = date(reference_date.year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(reference_date.year, reference_date.month + 1, 1) - timedelta(days=1)

    return start, end


def format_relative_date(target: date) -> str:
    """Format a date relative to today (e.g., 'in 3 days', '2 days ago')."""
    diff = days_until(target)

    if diff == 0:
        return "today"
    elif diff == 1:
        return "tomorrow"
    elif diff == -1:
        return "yesterday"
    elif diff > 0:
        if diff <= 7:
            return f"in {diff} days"
        elif diff <= 14:
            weeks = diff // 7
            return f"in {weeks} week{'s' if weeks > 1 else ''}"
        else:
            return f"on {format_date(target, 'short')}"
    else:
        abs_diff = abs(diff)
        if abs_diff <= 7:
            return f"{abs_diff} days ago"
        elif abs_diff <= 14:
            weeks = abs_diff // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        else:
            return f"on {format_date(target, 'short')}"


def get_deadline_urgency(due_date: date) -> str:
    """
    Get urgency level for a deadline.

    Returns: 'overdue', 'urgent', 'soon', 'upcoming', or 'normal'
    """
    days = days_until(due_date)

    if days < 0:
        return 'overdue'
    elif days <= 3:
        return 'urgent'
    elif days <= 7:
        return 'soon'
    elif days <= 14:
        return 'upcoming'
    else:
        return 'normal'


def date_range(start: date, end: date) -> List[date]:
    """Generate a list of dates from start to end (inclusive)."""
    dates = []
    current = start
    while current <= end:
        dates.append(current)
        current += timedelta(days=1)
    return dates


def parse_date_range(range_string: str) -> Optional[tuple]:
    """
    Parse a date range string.

    Formats:
    - "01/15/2024 - 01/30/2024"
    - "01/15/2024 to 01/30/2024"
    """
    separators = [' - ', ' to ', '-']

    for sep in separators:
        if sep in range_string:
            parts = range_string.split(sep)
            if len(parts) == 2:
                start = parse_date(parts[0])
                end = parse_date(parts[1])
                if start and end:
                    return (start, end)

    return None
