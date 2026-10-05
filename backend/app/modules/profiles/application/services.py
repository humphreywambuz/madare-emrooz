"""Profile and medical history use cases. Depend only on ports, never on Flask or SQLAlchemy."""
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from app.modules.audit.application.trail import AuditEvent, AuditTrail
from app.modules.audit.domain.enums import AuditEventType
from app.modules.profiles.domain.entities import MedicalHistory, Profile
from app.modules.profiles.domain.enums import BloodType, HomePath, JoinGoal, ReproductiveStatus
from app.modules.profiles.domain.rules import age_on
from app.shared.application.clock import clinic_today
from app.shared.application.context import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import NotFoundError

from .ports import MedicalHistoryRepository, ProfileRepository


@dataclass(frozen=True)
class ProfileView:
    user_id: uuid.UUID
    first_name: str
    last_name: str
    join_goal: JoinGoal
    national_code: str | None
    birth_date: date | None
    age: int | None
    height_cm: Decimal | None
    initial_weight_kg: Decimal | None
    mother_blood_type: BloodType | None
    spouse_blood_type: BloodType | None
    reproductive_status: ReproductiveStatus | None
    rh_incompatibility_risk: bool
    home: HomePath

    @classmethod
    def of(cls, profile: Profile, today: date) -> "ProfileView":
        return cls(
            user_id=profile.user_id,
            first_name=profile.first_name,
            last_name=profile.last_name,
            join_goal=profile.join_goal,
            national_code=profile.national_code,
            birth_date=profile.birth_date,
            age=age_on(profile.birth_date, today) if profile.birth_date else None,
            height_cm=profile.height_cm,
            initial_weight_kg=profile.initial_weight_kg,
            mother_blood_type=profile.mother_blood_type,
            spouse_blood_type=profile.father_blood_type,
            reproductive_status=profile.reproductive_status,
            rh_incompatibility_risk=profile.rh_incompatibility_risk,
            home=profile.home,
        )


class ProfileService:
    def __init__(
        self,
        profiles: ProfileRepository,
        histories: MedicalHistoryRepository,
        audit: AuditTrail,
        uow: UnitOfWork,
        today: Callable[[], date] = clinic_today,
    ):
        self._profiles = profiles
        self._histories = histories
        self._audit = audit
        self._uow = uow
        self._today = today

    # --- profile -----------------------------------------------------------------

    def get_profile(self, user_id: uuid.UUID) -> ProfileView:
        """Raises NotFoundError for a new user: the app then starts onboarding."""
        profile = self._profiles.get(user_id)
        if profile is None:
            raise NotFoundError("You have not created a profile yet.")
        return ProfileView.of(profile, self._today())

    def find_profile(self, user_id: uuid.UUID) -> ProfileView | None:
        profile = self._profiles.get(user_id)
        return ProfileView.of(profile, self._today()) if profile else None

    def save_profile(self, actor: Actor, values: dict[str, Any]) -> tuple[ProfileView, bool]:
        """Create or replace the signed-in user's profile. Returns (profile, created)."""
        values = dict(values)
        values["father_blood_type"] = values.pop("spouse_blood_type", None)
        profile = Profile(user_id=actor.user_id, **values)
        today = self._today()
        profile.validate(today)
        created = self._profiles.get(actor.user_id) is None
        self._profiles.save(profile)
        self._record(actor, AuditEventType.PROFILE_CREATED if created else AuditEventType.RECORD_UPDATED, "profile")
        self._uow.commit()
        return ProfileView.of(profile, today), created

    def record_delivery(self, user_id: uuid.UUID) -> None:
        """Called when her pregnancy ends with a birth; the caller's unit of work commits."""
        profile = self._profiles.get(user_id)
        if profile is not None:
            profile.record_delivery()
            self._profiles.save(profile)

    # --- medical history ---------------------------------------------------------

    def get_medical_history(self, user_id: uuid.UUID) -> MedicalHistory:
        history = self._histories.get(user_id)
        if history is None:
            raise NotFoundError("No medical history has been saved yet.")
        return history

    def find_medical_history(self, user_id: uuid.UUID) -> MedicalHistory | None:
        return self._histories.get(user_id)

    def save_medical_history(self, actor: Actor, values: dict[str, Any]) -> tuple[MedicalHistory, bool]:
        history = MedicalHistory(user_id=actor.user_id, **values)
        created = self._histories.get(actor.user_id) is None
        self._histories.save(history)
        self._record(actor, AuditEventType.RECORD_UPDATED, "medical_history")
        self._uow.commit()
        return history, created

    def _record(self, actor: Actor, event_type: AuditEventType, resource: str) -> None:
        self._audit.record(
            AuditEvent(
                event_type,
                actor_id=actor.user_id,
                patient_id=actor.user_id,
                resource_type=resource,
                resource_id=str(actor.user_id),
                ip_address=actor.context.ip_address,
                user_agent=actor.context.user_agent,
            )
        )
