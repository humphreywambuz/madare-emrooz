from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.pregnancy.domain.entities import Pregnancy
from app.modules.pregnancy.domain.enums import ConceptionType, PregnancyStatus
from app.modules.pregnancy.infrastructure.repository import SqlAlchemyPregnancyRepository


def new_pregnancy(user_id):
    return Pregnancy.start(
        user_id=user_id,
        lmp_date=date(2026, 1, 1),
        conception_type=ConceptionType.ASSISTED,
        today=date(2026, 3, 1),
    )


def test_round_trip(session, make_user):
    repo = SqlAlchemyPregnancyRepository(session)
    user = make_user()
    pregnancy = new_pregnancy(user.id)
    repo.add(pregnancy)

    loaded = repo.get_active_for_user(user.id)
    assert loaded == pregnancy

    loaded.end(status=PregnancyStatus.ENDED, on=date(2026, 3, 2))
    repo.save(loaded)
    assert repo.get_active_for_user(user.id) is None


def test_database_allows_one_active_pregnancy(session, make_user):
    repo = SqlAlchemyPregnancyRepository(session)
    user = make_user()
    repo.add(new_pregnancy(user.id))
    with pytest.raises(IntegrityError):
        repo.add(new_pregnancy(user.id))
