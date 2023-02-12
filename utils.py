import datetime
from datetime import timedelta


def date_range(start_date, end_date):
    """Generate a list of dates between start_date and end_date"""

    start_date = datetime.date.fromisoformat(start_date)
    end_date = datetime.date.fromisoformat(end_date)
    current_date = start_date
    while current_date <= end_date:
        yield current_date.strftime('%Y-%m-%d')
        current_date += timedelta(days=1)
