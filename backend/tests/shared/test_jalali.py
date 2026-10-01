from datetime import date

import pytest

from app.shared.domain.jalali import format_jalali, to_jalali


@pytest.mark.parametrize(
    ("gregorian", "jalali"),
    [
        (date(2024, 3, 20), (1403, 1, 1)),   # Nowruz 1403
        (date(2023, 3, 21), (1402, 1, 1)),   # Nowruz 1402
        (date(2025, 3, 21), (1404, 1, 1)),   # Nowruz 1404
        (date(2026, 10, 1), (1405, 7, 9)),
        (date(2025, 3, 20), (1403, 12, 30)), # 1403 is a leap year
        (date(2000, 1, 1), (1378, 10, 11)),
    ],
)
def test_to_jalali(gregorian, jalali):
    assert to_jalali(gregorian) == jalali


def test_format_jalali():
    assert format_jalali(date(2026, 10, 1)) == "۹ مهر ۱۴۰۵"
