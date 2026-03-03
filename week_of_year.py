# Overwrite existing file with a small utility to get the ISO week of a date.
from __future__ import annotations
import sys
from datetime import datetime, date


def week_of_year(d: date) -> tuple[int, int]:
    """Return (ISO-year, ISO-week) for the given date."""
    y, w, _ = d.isocalendar()
    return y, w


def parse_date(s: str) -> date:
    """Parse common date formats into a date object.

    Accepted formats: YYYY-MM-DD, YYYY/MM/DD, DD-MM-YYYY, DD/MM/YYYY
    """
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {s}. Use YYYY-MM-DD or DD-MM-YYYY")


if __name__ == "__main__":
    # If a date is provided as the first argument, parse it; otherwise use today.
    if len(sys.argv) > 1:
        s = sys.argv[1]
        try:
            d = parse_date(s)
        except ValueError as e:
            print(e)
            sys.exit(1)
    else:
        d = date.today()

    y, w = week_of_year(d)
    print(f"{d.isoformat()} is in ISO week {w}, year {y}")

