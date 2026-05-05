# application/util/date_utils.py

# Partial Imports
from datetime import date, datetime


def parse_date(s: str) -> date:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass

    raise ValueError(f"ERROR: Unrecognized date format: {s}")
