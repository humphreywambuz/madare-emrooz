import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.modules.pregnancy.domain.entities import Pregnancy
from app.modules.pregnancy.domain.enums import PregnancyStatus

from .models import PregnancyModel

_FIELDS = (
    "id",
    "user_id",
    "lmp_date",
    "avg_cycle_length_days",
    "conception_type",
    "estimated_due_date",
    "care_provider_type",
    "care_provider_name",
    "status",
    "ended_on",
)


def _to_entity(row: PregnancyModel) -> Pregnancy:
    return Pregnancy(**{f: getattr(row, f) for f in _FIELDS})


class SqlAlchemyPregnancyRepository:
    """Implements ``application.ports.PregnancyRepository``."""

    def __init__(self, session: Session):
        self._session = session

    def get_active_for_user(self, user_id: uuid.UUID) -> Pregnancy | None:
        row = self._session.scalar(
            sa.select(PregnancyModel).where(
                PregnancyModel.user_id == user_id,
                PregnancyModel.status == PregnancyStatus.ACTIVE,
            )
        )
        return _to_entity(row) if row else None

    def add(self, pregnancy: Pregnancy) -> None:
        self._session.add(PregnancyModel(**{f: getattr(pregnancy, f) for f in _FIELDS}))
        self._session.flush()

    def save(self, pregnancy: Pregnancy) -> None:
        row = self._session.get(PregnancyModel, pregnancy.id)
        for f in _FIELDS:
            setattr(row, f, getattr(pregnancy, f))
        self._session.flush()
