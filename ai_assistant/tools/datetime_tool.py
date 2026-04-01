"""Date and time tool - current time, timezone conversions, date math."""

from datetime import datetime, timedelta, timezone
import calendar


def get_current_time(tz_offset: int = 0) -> str:
    """Get the current date and time."""
    tz = timezone(timedelta(hours=tz_offset))
    now = datetime.now(tz)
    tz_name = f"UTC{tz_offset:+d}" if tz_offset else "UTC"
    return (
        f"Current date and time ({tz_name}):\n"
        f"  Date: {now.strftime('%A, %B %d, %Y')}\n"
        f"  Time: {now.strftime('%I:%M:%S %p')}\n"
        f"  ISO:  {now.isoformat()}\n"
        f"  Unix: {int(now.timestamp())}"
    )


def date_difference(date1: str, date2: str) -> str:
    """Calculate the difference between two dates."""
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%B %d, %Y", "%b %d, %Y"]

    d1 = d2 = None
    for fmt in formats:
        try:
            d1 = datetime.strptime(date1, fmt)
            break
        except ValueError:
            continue

    for fmt in formats:
        try:
            d2 = datetime.strptime(date2, fmt)
            break
        except ValueError:
            continue

    if not d1:
        return f"Error: Could not parse date '{date1}'. Use YYYY-MM-DD format."
    if not d2:
        return f"Error: Could not parse date '{date2}'. Use YYYY-MM-DD format."

    diff = abs(d2 - d1)
    days = diff.days
    weeks = days // 7
    months = days // 30
    years = days // 365

    return (
        f"Difference between {d1.strftime('%Y-%m-%d')} and {d2.strftime('%Y-%m-%d')}:\n"
        f"  {days} days\n"
        f"  {weeks} weeks and {days % 7} days\n"
        f"  ~{months} months\n"
        f"  ~{years} years and {days % 365} days"
    )


def add_to_date(date_str: str, days: int = 0, weeks: int = 0, months: int = 0) -> str:
    """Add time to a date."""
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"]

    d = None
    for fmt in formats:
        try:
            d = datetime.strptime(date_str, fmt)
            break
        except ValueError:
            continue

    if not d:
        return f"Error: Could not parse date '{date_str}'. Use YYYY-MM-DD format."

    total_days = days + (weeks * 7) + (months * 30)
    result = d + timedelta(days=total_days)

    return (
        f"Starting from: {d.strftime('%A, %B %d, %Y')}\n"
        f"Adding: {days} days, {weeks} weeks, {months} months\n"
        f"Result: {result.strftime('%A, %B %d, %Y')} ({result.strftime('%Y-%m-%d')})"
    )


def show_calendar(year: int, month: int) -> str:
    """Show a calendar for a given month."""
    try:
        cal = calendar.month(year, month)
        return f"Calendar:\n{cal}"
    except (ValueError, calendar.IllegalMonthError) as e:
        return f"Error: {e}"


TOOL_DEFINITION = {
    "name": "datetime_tool",
    "description": (
        "Get current date/time, calculate date differences, add time to dates, "
        "or show a calendar. Supports timezone offsets."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["now", "difference", "add", "calendar"],
                "description": "The date/time action to perform",
            },
            "tz_offset": {
                "type": "integer",
                "description": "UTC timezone offset in hours (for 'now')",
            },
            "date1": {
                "type": "string",
                "description": "First date in YYYY-MM-DD format (for 'difference')",
            },
            "date2": {
                "type": "string",
                "description": "Second date in YYYY-MM-DD format (for 'difference')",
            },
            "date": {
                "type": "string",
                "description": "Date in YYYY-MM-DD format (for 'add')",
            },
            "days": {
                "type": "integer",
                "description": "Days to add (for 'add')",
            },
            "weeks": {
                "type": "integer",
                "description": "Weeks to add (for 'add')",
            },
            "months": {
                "type": "integer",
                "description": "Months to add (for 'add')",
            },
            "year": {
                "type": "integer",
                "description": "Year (for 'calendar')",
            },
            "month": {
                "type": "integer",
                "description": "Month 1-12 (for 'calendar')",
            },
        },
        "required": ["action"],
    },
}


def handle(input_data: dict) -> str:
    """Handle a tool call from the API."""
    action = input_data["action"]

    if action == "now":
        return get_current_time(input_data.get("tz_offset", 0))
    elif action == "difference":
        return date_difference(input_data.get("date1", ""), input_data.get("date2", ""))
    elif action == "add":
        return add_to_date(
            input_data.get("date", ""),
            input_data.get("days", 0),
            input_data.get("weeks", 0),
            input_data.get("months", 0),
        )
    elif action == "calendar":
        return show_calendar(input_data.get("year", 2024), input_data.get("month", 1))
    else:
        return f"Error: Unknown action '{action}'"
