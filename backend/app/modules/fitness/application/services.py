"""Fitness use cases. Depend only on ports, never on Flask or SQLAlchemy."""
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from app.modules.audit.application.trail import AuditEvent, AuditTrail
from app.modules.audit.domain.enums import AuditEventType
from app.modules.fitness.domain.entities import FitnessProfile
from app.modules.fitness.domain.enums import FitnessGoal
from app.shared.application.access import PatientAccess
from app.shared.application.context import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import NotFoundError


class FitnessProfileRepository(Protocol):
    def get(self, user_id: uuid.UUID) -> FitnessProfile | None: ...

    def save(self, profile: FitnessProfile) -> None: ...


@dataclass(frozen=True)
class FitnessView:
    goal: FitnessGoal
    goal_note: str | None
    specialist_visit_completed: bool
    specialist_visit_at: datetime | None
    dashboard_unlocked: bool

    @classmethod
    def of(cls, p: FitnessProfile) -> "FitnessView":
        return cls(p.goal, p.goal_note, p.specialist_visit_completed, p.specialist_visit_at, p.dashboard_unlocked)


class FitnessService:
    def __init__(
        self,
        *,
        profiles: FitnessProfileRepository,
        access: PatientAccess,
        audit: AuditTrail,
        uow: UnitOfWork,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        self._profiles = profiles
        self._access = access
        self._audit = audit
        self._uow = uow
        self._now = now

    def get_own(self, user_id: uuid.UUID) -> FitnessView:
        return FitnessView.of(self._require(user_id))

    def find(self, user_id: uuid.UUID) -> FitnessView | None:
        profile = self._profiles.get(user_id)
        return FitnessView.of(profile) if profile else None

    def save_own(self, actor: Actor, goal: FitnessGoal, goal_note: str | None) -> tuple[FitnessView, bool]:
        """Set her goal; the specialist visit, recorded by staff, is kept."""
        profile = self._profiles.get(actor.user_id)
        created = profile is None
        if created:
            profile = FitnessProfile(actor.user_id, goal, goal_note)
        else:
            profile.update_goal(goal, goal_note)
        self._profiles.save(profile)
        self._uow.commit()
        return FitnessView.of(profile), created

    def record_specialist_visit(self, actor: Actor, patient_id: uuid.UUID) -> FitnessView:
        self._access.require_record_access(actor, patient_id)
        profile = self._require(patient_id)
        profile.record_specialist_visit(self._now())
        self._profiles.save(profile)
        self._audit.record(
            AuditEvent(
                AuditEventType.RECORD_UPDATED,
                actor_id=actor.user_id,
                patient_id=patient_id,
                resource_type="fitness_profile",
                resource_id=str(patient_id),
                ip_address=actor.context.ip_address,
                user_agent=actor.context.user_agent,
                details={"specialist_visit_completed": True},
            )
        )
        self._uow.commit()
        return FitnessView.of(profile)

    def _require(self, user_id: uuid.UUID) -> FitnessProfile:
        profile = self._profiles.get(user_id)
        if profile is None:
            raise NotFoundError("No fitness profile yet.")
        return profile
