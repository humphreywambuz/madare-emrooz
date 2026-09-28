"""Use cases tested with in-memory fakes: no database, no Flask."""
import uuid
from datetime import date

import pytest

from app.modules.pregnancy.application.services import PregnancyService, StartPregnancy
from app.modules.pregnancy.domain.enums import ConceptionType, PregnancyStatus
from app.shared.domain.errors import ConflictError, NotFoundError


class FakeRepository:
    def __init__(self):
        self.items = {}

    def get_active_for_user(self, user_id):
        return next((p for p in self.items.values() if p.user_id == user_id and p.is_active), None)

    def add(self, pregnancy):
        self.items[pregnancy.id] = pregnancy

    def save(self, pregnancy):
        self.items[pregnancy.id] = pregnancy


class FakeUnitOfWork:
    commits = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass


@pytest.fixture()
def service():
    return PregnancyService(FakeRepository(), FakeUnitOfWork(), today=lambda: date(2026, 4, 1))


def command(user_id):
    return StartPregnancy(
        user_id=user_id, lmp_date=date(2026, 1, 1), conception_type=ConceptionType.NATURAL
    )


def test_start_and_get_active(service):
    user_id = uuid.uuid4()
    started = service.start(command(user_id))
    assert started.gestational_week == 12
    assert service.get_active(user_id) == started


def test_cannot_start_second_active_pregnancy(service):
    user_id = uuid.uuid4()
    service.start(command(user_id))
    with pytest.raises(ConflictError):
        service.start(command(user_id))


def test_end_active_then_start_again(service):
    user_id = uuid.uuid4()
    service.start(command(user_id))
    ended = service.end_active(user_id, PregnancyStatus.DELIVERED)
    assert ended.status is PregnancyStatus.DELIVERED
    with pytest.raises(NotFoundError):
        service.get_active(user_id)
    service.start(command(user_id))
