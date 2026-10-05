"""The clinic's calendar. Mothers and staff are in Iran, so "today" is the date in Tehran,
not on the server (which runs in UTC): between 00:00 and 03:30 Tehran time the two differ."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

CLINIC_TIMEZONE = ZoneInfo("Asia/Tehran")


def clinic_today() -> date:
    return datetime.now(CLINIC_TIMEZONE).date()
