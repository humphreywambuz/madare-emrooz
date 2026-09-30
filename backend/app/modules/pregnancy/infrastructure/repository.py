import uuid

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.pregnancy.domain.entities import Pregnancy
from app.modules.pregnancy.domain.enums import PregnancyStatus
from app.shared.domain.errors import ConflictError

from .models import PregnancyModel

ONE_ACTIVE_PER_USER = "uq_pregnancies_one_active_per_user"

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
        row = PregnancyModel(**{f: getattr(pregnancy, f) for f in _FIELDS})
        try:
            # A savepoint keeps the session usable if the insert is rejected.
            with self._session.begin_nested():
                self._session.add(row)
        except IntegrityError as exc:
            # A concurrent request started a pregnancy between the service's
            # "already active?" check and this insert.
            if getattr(exc.orig.diag, "constraint_name", None) == ONE_ACTIVE_PER_USER:
                raise ConflictError("You already have an active pregnancy.") from exc
            raise

    def save(self, pregnancy: Pregnancy) -> None:
        row = self._session.get(PregnancyModel, pregnancy.id)
        for f in _FIELDS:
            setattr(row, f, getattr(pregnancy, f))
        self._session.flush()
