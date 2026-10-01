"""Gregorian → Jalali (Solar Hijri) dates, for pages shown to people in Iran."""
from datetime import date

PERSIAN_MONTHS = (
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
)
_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_DAYS_BEFORE_MONTH = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)


def to_jalali(d: date) -> tuple[int, int, int]:
    """Return (year, month, day) in the Jalali calendar. Valid for 1600–3000 CE."""
    gy2 = d.year + 1 if d.month > 2 else d.year
    days = (
        355666 + 365 * d.year + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400
        + d.day + _DAYS_BEFORE_MONTH[d.month - 1]
    )
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        return jy, 1 + days // 31, 1 + days % 31
    return jy, 7 + (days - 186) // 30, 1 + (days - 186) % 30


def persian_digits(value: object) -> str:
    return str(value).translate(_PERSIAN_DIGITS)


def format_jalali(d: date) -> str:
    """e.g. ۱۲ اردیبهشت ۱۴۰۵"""
    year, month, day = to_jalali(d)
    return f"{persian_digits(day)} {PERSIAN_MONTHS[month - 1]} {persian_digits(year)}"
