"""Rehabilitation use cases. Depend only on ports, never on Flask or SQLAlchemy."""
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

from app.modules.audit.application.trail import AuditEvent, AuditTrail
from app.modules.audit.domain.enums import AuditEventType
from app.modules.rehabilitation.domain.entities import RehabProfile
from app.modules.rehabilitation.domain.policies import is_advanced_locked
from app.shared.application.access import PatientAccess
from app.shared.application.context import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import NotFoundError


class RehabProfileRepository(Protocol):
    def get(self, user_id: uuid.UUID) -> RehabProfile | None: ...

    def save(self, profile: RehabProfile) -> None: ...


@dataclass(frozen=True)
class RehabView:
    profile: RehabProfile
    # Advanced exercises stay locked until the visit and the doctor's approval.
    is_advanced_locked: bool


class RehabService:
    def __init__(
        self,
        *,
        profiles: RehabProfileRepository,
        has_plan_approval: Callable[[uuid.UUID], bool],
        require_document_of: Callable[[uuid.UUID, uuid.UUID], object],
        access: PatientAccess,
        audit: AuditTrail,
        uow: UnitOfWork,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        self._profiles = profiles
        self._has_plan_approval = has_plan_approval
        self._require_document_of = require_document_of
        self._access = access
        self._audit = audit
        self._uow = uow
        self._now = now

    def get_own(self, user_id: uuid.UUID) -> RehabView:
        return self._view(self._require(user_id))

    def find(self, user_id: uuid.UUID) -> RehabView | None:
        profile = self._profiles.get(user_id)
        return self._view(profile) if profile else None

    def save_own(self, actor: Actor, answers: dict[str, Any]) -> tuple[RehabView, bool]:
        profile = self._profiles.get(actor.user_id)
        created = profile is None
        if created:
            profile = RehabProfile.from_answers(actor.user_id, answers)
        else:
            profile.answer(answers)
        self._profiles.save(profile)
        self._uow.commit()
        return self._view(profile), created

    def record_specialist_visit(self, actor: Actor, patient_id: uuid.UUID) -> RehabView:
        self._access.require_record_access(actor, patient_id)
        profile = self._require(patient_id)
        profile.record_specialist_visit(self._now())
        return self._save_by_staff(actor, profile, {"specialist_visit_completed": True})

    def attach_imaging(self, actor: Actor, patient_id: uuid.UUID, document_id: uuid.UUID) -> RehabView:
        """Her midwife links an uploaded X-ray or MRI to the rehabilitation profile."""
        self._access.require_record_access(actor, patient_id)
        profile = self._require(patient_id)
        self._require_document_of(patient_id, document_id)
        profile.imaging_document_id = document_id
        return self._save_by_staff(actor, profile, {"imaging_document_id": str(document_id)})

    def _save_by_staff(self, actor: Actor, profile: RehabProfile, details: dict) -> RehabView:
        self._profiles.save(profile)
        self._audit.record(
            AuditEvent(
                AuditEventType.RECORD_UPDATED,
                actor_id=actor.user_id,
                patient_id=profile.user_id,
                resource_type="rehab_profile",
                resource_id=str(profile.user_id),
                ip_address=actor.context.ip_address,
                user_agent=actor.context.user_agent,
                details=details,
            )
        )
        self._uow.commit()
        return self._view(profile)

    def _view(self, profile: RehabProfile) -> RehabView:
        locked = is_advanced_locked(
            specialist_visit_completed=profile.specialist_visit_completed,
            has_active_approval=self._has_plan_approval(profile.user_id),
        )
        return RehabView(profile, locked)

    def _require(self, user_id: uuid.UUID) -> RehabProfile:
        profile = self._profiles.get(user_id)
        if profile is None:
            raise NotFoundError("No rehabilitation profile yet.")
        return profile
