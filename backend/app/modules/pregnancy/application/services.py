"""Pregnancy use cases. Depend only on ports, never on Flask or SQLAlchemy."""
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from app.modules.pregnancy.domain.entities import Pregnancy
from app.modules.pregnancy.domain.enums import CareProviderType, ConceptionType, PregnancyStatus
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import ConflictError, NotFoundError

from .ports import PregnancyRepository


@dataclass(frozen=True)
class StartPregnancy:
    user_id: uuid.UUID
    lmp_date: date
    conception_type: ConceptionType
    avg_cycle_length_days: int = 28
    care_provider_type: CareProviderType | None = None
    care_provider_name: str | None = None


@dataclass(frozen=True)
class PregnancyView:
    id: uuid.UUID
    lmp_date: date
    avg_cycle_length_days: int
    conception_type: ConceptionType
    estimated_due_date: date
    gestational_week: int
    care_provider_type: CareProviderType | None
    care_provider_name: str | None
    status: PregnancyStatus

    @classmethod
    def of(cls, pregnancy: Pregnancy, today: date) -> "PregnancyView":
        return cls(
            id=pregnancy.id,
            lmp_date=pregnancy.lmp_date,
            avg_cycle_length_days=pregnancy.avg_cycle_length_days,
            conception_type=pregnancy.conception_type,
            estimated_due_date=pregnancy.estimated_due_date,
            gestational_week=pregnancy.gestational_week(today),
            care_provider_type=pregnancy.care_provider_type,
            care_provider_name=pregnancy.care_provider_name,
            status=pregnancy.status,
        )


class PregnancyService:
    def __init__(
        self,
        pregnancies: PregnancyRepository,
        uow: UnitOfWork,
        today: Callable[[], date] = date.today,
    ):
        self._pregnancies = pregnancies
        self._uow = uow
        self._today = today

    def start(self, command: StartPregnancy) -> PregnancyView:
        if self._pregnancies.get_active_for_user(command.user_id) is not None:
            raise ConflictError("You already have an active pregnancy.")
        today = self._today()
        pregnancy = Pregnancy.start(
            user_id=command.user_id,
            lmp_date=command.lmp_date,
            conception_type=command.conception_type,
            avg_cycle_length_days=command.avg_cycle_length_days,
            care_provider_type=command.care_provider_type,
            care_provider_name=command.care_provider_name,
            today=today,
        )
        self._pregnancies.add(pregnancy)
        self._uow.commit()
        return PregnancyView.of(pregnancy, today)

    def get_active(self, user_id: uuid.UUID) -> PregnancyView:
        pregnancy = self._require_active(user_id)
        return PregnancyView.of(pregnancy, self._today())

    def end_active(self, user_id: uuid.UUID, status: PregnancyStatus) -> PregnancyView:
        pregnancy = self._require_active(user_id)
        today = self._today()
        pregnancy.end(status=status, on=today)
        self._pregnancies.save(pregnancy)
        self._uow.commit()
        return PregnancyView.of(pregnancy, today)

    def _require_active(self, user_id: uuid.UUID) -> Pregnancy:
        pregnancy = self._pregnancies.get_active_for_user(user_id)
        if pregnancy is None:
            raise NotFoundError("You have no active pregnancy.")
        return pregnancy
