import uuid
from datetime import date, timedelta

import pytest

from app.modules.pregnancy.domain.entities import Pregnancy, calculate_due_date
from app.modules.pregnancy.domain.enums import ConceptionType, PregnancyStatus
from app.shared.domain.errors import ValidationError

TODAY = date(2026, 4, 1)


def start(**overrides):
    kwargs = dict(
        user_id=uuid.uuid4(),
        lmp_date=date(2026, 1, 1),
        conception_type=ConceptionType.NATURAL,
        today=TODAY,
    )
    kwargs.update(overrides)
    return Pregnancy.start(**kwargs)


def test_due_date_follows_naegele_rule():
    assert calculate_due_date(date(2026, 1, 1)) == date(2026, 10, 8)
    assert calculate_due_date(date(2026, 1, 1), cycle_length_days=35) == date(2026, 10, 15)


def test_start_computes_due_date_and_week():
    pregnancy = start()
    assert pregnancy.estimated_due_date == date(2026, 10, 8)
    assert pregnancy.is_active
    assert pregnancy.gestational_week(on=date(2026, 1, 1) + timedelta(weeks=12, days=3)) == 12


def test_week_never_goes_below_zero():
    # A 45-day cycle moves the due date 17 days later, so counting back from it right after
    # the LMP would give week -3.
    pregnancy = start(lmp_date=TODAY - timedelta(days=2), avg_cycle_length_days=45)
    assert pregnancy.gestational_age_days(on=TODAY) == 0
    assert pregnancy.gestational_week(on=TODAY) == 0
    assert pregnancy.gestational_week(on=TODAY + timedelta(weeks=5)) == 2


@pytest.mark.parametrize(
    "overrides",
    [
        {"lmp_date": TODAY + timedelta(days=1)},
        {"lmp_date": TODAY - timedelta(weeks=45)},
        {"avg_cycle_length_days": 60},
    ],
)
def test_start_rejects_invalid_input(overrides):
    with pytest.raises(ValidationError):
        start(**overrides)


def test_end_pregnancy():
    pregnancy = start()
    pregnancy.end(status=PregnancyStatus.DELIVERED, on=TODAY)
    assert pregnancy.status is PregnancyStatus.DELIVERED
    assert pregnancy.ended_on == TODAY
    with pytest.raises(ValidationError):
        pregnancy.end(status=PregnancyStatus.ENDED, on=TODAY)
