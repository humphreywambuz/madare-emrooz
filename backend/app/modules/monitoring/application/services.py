"""Daily monitoring use cases: the mother reports bleeding, her midwife records vitals.

Depend only on ports, never on Flask or SQLAlchemy.
"""
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from app.modules.audit.application.trail import AuditEvent, AuditTrail
from app.modules.audit.domain.enums import AuditEventType
from app.modules.monitoring.domain.entities import MEASUREMENTS, DailyLog
from app.shared.application.access import PatientAccess
from app.shared.application.context import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import ValidationError

from .ports import DailyLogRepository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MonitoringService:
    def __init__(
        self,
        *,
        logs: DailyLogRepository,
        active_pregnancy_id: Callable[[uuid.UUID], uuid.UUID | None],
        on_bleeding: Callable[[uuid.UUID, uuid.UUID], None],
        access: PatientAccess,
        audit: AuditTrail,
        uow: UnitOfWork,
        now: Callable[[], datetime] = _utcnow,
    ):
        self._logs = logs
        self._active_pregnancy_id = active_pregnancy_id
        self._on_bleeding = on_bleeding
        self._access = access
        self._audit = audit
        self._uow = uow
        self._now = now

    def report_bleeding(self, actor: Actor, has_spotting_or_bleeding: bool) -> DailyLog:
        """The mother's own report during pregnancy. A yes raises a red alert for her midwife
        (or for the admins while she has none) in the same transaction."""
        pregnancy_id = self._active_pregnancy_id(actor.user_id)
        if pregnancy_id is None:
            raise ValidationError("Bleeding can be reported during an active pregnancy.")
        log = DailyLog(
            patient_id=actor.user_id,
            recorded_by_id=actor.user_id,
            recorded_at=self._now(),
            pregnancy_id=pregnancy_id,
            has_spotting_or_bleeding=has_spotting_or_bleeding,
        )
        self._logs.add(log)
        if log.is_red_alert:
            self._on_bleeding(actor.user_id, log.id)
        self._uow.commit()
        return log

    def own_logs(self, user_id: uuid.UUID, limit: int = 100) -> list[DailyLog]:
        return self._logs.list_for_patient(user_id, limit)

    def record_for_patient(self, actor: Actor, patient_id: uuid.UUID, values: dict[str, Any]) -> DailyLog:
        """The midwife records vitals and symptoms for one of her mothers."""
        self._access.require_record_access(actor, patient_id)
        unknown = set(values) - set(MEASUREMENTS) - {"has_spotting_or_bleeding"}
        if unknown:
            raise ValidationError(f"Unknown fields: {', '.join(sorted(unknown))}.")
        log = DailyLog(
            patient_id=patient_id,
            recorded_by_id=actor.user_id,
            recorded_at=self._now(),
            pregnancy_id=self._active_pregnancy_id(patient_id),
            **values,
        )
        log.validate()
        self._logs.add(log)
        self._audit.record(
            AuditEvent(
                AuditEventType.RECORD_CREATED,
                actor_id=actor.user_id,
                patient_id=patient_id,
                resource_type="daily_log",
                resource_id=str(log.id),
                ip_address=actor.context.ip_address,
                user_agent=actor.context.user_agent,
            )
        )
        self._uow.commit()
        return log

    def logs_for_patient(self, actor: Actor, patient_id: uuid.UUID, limit: int = 100) -> list[DailyLog]:
        self._access.require_record_access(actor, patient_id)
        logs = self._logs.list_for_patient(patient_id, limit)
        self._access.record_viewed(actor, patient_id, "daily_logs")
        return logs
