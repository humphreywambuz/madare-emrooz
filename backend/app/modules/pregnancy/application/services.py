"""Pregnancy use cases. Depend only on ports, never on Flask or SQLAlchemy."""
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

from app.modules.audit.application.trail import AuditEvent, AuditTrail
from app.modules.audit.domain.enums import AuditEventType
from app.modules.pregnancy.domain.entities import Pregnancy
from app.modules.pregnancy.domain.enums import CareProviderType, ConceptionType, PregnancyStatus
from app.shared.application.access import PatientAccess
from app.shared.application.context import Actor
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
    due_date_source: str  # "lmp" or "clinician"
    due_date_corrected_at: datetime | None

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
            due_date_source=pregnancy.due_date_source,
            due_date_corrected_at=pregnancy.due_date_corrected_at,
        )


class PregnancyService:
    def __init__(
        self,
        pregnancies: PregnancyRepository,
        uow: UnitOfWork,
        today: Callable[[], date] = date.today,
        on_delivered: Callable[[uuid.UUID], None] | None = None,
        audit: AuditTrail | None = None,
        access: PatientAccess | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        self._pregnancies = pregnancies
        self._uow = uow
        self._today = today
        self._on_delivered = on_delivered
        self._audit = audit
        self._access = access
        self._now = now

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
        if status is PregnancyStatus.DELIVERED and self._on_delivered:
            self._on_delivered(user_id)  # in the same transaction
        self._uow.commit()
        return PregnancyView.of(pregnancy, today)

    def correct(self, actor: Actor, changes: dict[str, Any]) -> PregnancyView:
        """The mother fixes what she entered, e.g. a wrong LMP, without ending the pregnancy."""
        pregnancy = self._require_active(actor.user_id)
        before = pregnancy.estimated_due_date
        today = self._today()
        pregnancy.correct_details(today, **changes)
        self._pregnancies.save(pregnancy)
        self._record(actor, pregnancy, {
            "changed": sorted(changes),
            "due_date": {"from": before.isoformat(), "to": pregnancy.estimated_due_date.isoformat()},
        })
        self._uow.commit()
        return PregnancyView.of(pregnancy, today)

    def correct_due_date(
        self, actor: Actor, patient_id: uuid.UUID, due_date: date, reason: str | None
    ) -> PregnancyView:
        """Her midwife or a doctor sets the due date, e.g. from an ultrasound."""
        self._access.require_record_access(actor, patient_id)
        pregnancy = self._require_active(patient_id, "She has no active pregnancy.")
        before = pregnancy.estimated_due_date
        today = self._today()
        pregnancy.correct_due_date(due_date, by=actor.user_id, at=self._now(), today=today)
        self._pregnancies.save(pregnancy)
        self._record(actor, pregnancy, {
            "due_date": {"from": before.isoformat(), "to": due_date.isoformat()},
            "reason": reason,
        })
        self._uow.commit()
        return PregnancyView.of(pregnancy, today)

    def find_active(self, user_id: uuid.UUID) -> PregnancyView | None:
        pregnancy = self._pregnancies.get_active_for_user(user_id)
        return PregnancyView.of(pregnancy, self._today()) if pregnancy else None

    def active_pregnancy_id(self, user_id: uuid.UUID) -> uuid.UUID | None:
        pregnancy = self._pregnancies.get_active_for_user(user_id)
        return pregnancy.id if pregnancy else None

    def _require_active(
        self, user_id: uuid.UUID, message: str = "You have no active pregnancy."
    ) -> Pregnancy:
        pregnancy = self._pregnancies.get_active_for_user(user_id)
        if pregnancy is None:
            raise NotFoundError(message)
        return pregnancy

    def _record(self, actor: Actor, pregnancy: Pregnancy, details: dict) -> None:
        if self._audit is None:
            return
        self._audit.record(
            AuditEvent(
                AuditEventType.RECORD_UPDATED,
                actor_id=actor.user_id,
                patient_id=pregnancy.user_id,
                resource_type="pregnancy",
                resource_id=str(pregnancy.id),
                ip_address=actor.context.ip_address,
                user_agent=actor.context.user_agent,
                details=details,
            )
        )
