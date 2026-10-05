""""Today" is the date in Tehran, whatever the server's own time zone."""
from datetime import date, datetime, timezone

from app.shared.application import clock


def frozen_at(instant: datetime):
    class Frozen(datetime):
        @classmethod
        def now(cls, tz=None):
            return instant.astimezone(tz)

    return Frozen


def test_after_midnight_in_tehran_is_already_the_next_day(monkeypatch):
    # 21:00 UTC is 00:30 in Tehran (UTC+03:30, no daylight saving since 2022).
    monkeypatch.setattr(clock, "datetime", frozen_at(datetime(2026, 3, 20, 21, 0, tzinfo=timezone.utc)))
    assert clock.clinic_today() == date(2026, 3, 21)


def test_before_midnight_in_tehran_is_still_the_same_day(monkeypatch):
    monkeypatch.setattr(clock, "datetime", frozen_at(datetime(2026, 3, 20, 20, 29, tzinfo=timezone.utc)))
    assert clock.clinic_today() == date(2026, 3, 20)
