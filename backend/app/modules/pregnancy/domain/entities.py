"""Pregnancy aggregate (spec section 4). Pure Python: no Flask, no SQLAlchemy."""
import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta

from app.shared.domain.errors import ValidationError

from .enums import CareProviderType, ConceptionType, PregnancyStatus

PREGNANCY_LENGTH_DAYS = 280
STANDARD_CYCLE_DAYS = 28
MIN_CYCLE_DAYS, MAX_CYCLE_DAYS = 20, 45
# An LMP older than this cannot belong to an ongoing pregnancy.
MAX_PREGNANCY_DAYS = 44 * 7


def calculate_due_date(lmp_date: date, cycle_length_days: int = STANDARD_CYCLE_DAYS) -> date:
    """Naegele's rule, adjusted for cycle length."""
    return lmp_date + timedelta(
        days=PREGNANCY_LENGTH_DAYS + (cycle_length_days - STANDARD_CYCLE_DAYS)
    )


@dataclass
class Pregnancy:
    user_id: uuid.UUID
    lmp_date: date
    avg_cycle_length_days: int
    conception_type: ConceptionType
    estimated_due_date: date
    care_provider_type: CareProviderType | None = None
    care_provider_name: str | None = None
    status: PregnancyStatus = PregnancyStatus.ACTIVE
    ended_on: date | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    @classmethod
    def start(
        cls,
        *,
        user_id: uuid.UUID,
        lmp_date: date,
        conception_type: ConceptionType,
        today: date,
        avg_cycle_length_days: int = STANDARD_CYCLE_DAYS,
        care_provider_type: CareProviderType | None = None,
        care_provider_name: str | None = None,
    ) -> "Pregnancy":
        if lmp_date > today:
            raise ValidationError("The last menstrual period cannot be in the future.")
        if (today - lmp_date).days > MAX_PREGNANCY_DAYS:
            raise ValidationError("The last menstrual period is too long ago for an ongoing pregnancy.")
        if not MIN_CYCLE_DAYS <= avg_cycle_length_days <= MAX_CYCLE_DAYS:
            raise ValidationError(
                f"Cycle length must be between {MIN_CYCLE_DAYS} and {MAX_CYCLE_DAYS} days."
            )
        return cls(
            user_id=user_id,
            lmp_date=lmp_date,
            avg_cycle_length_days=avg_cycle_length_days,
            conception_type=conception_type,
            estimated_due_date=calculate_due_date(lmp_date, avg_cycle_length_days),
            care_provider_type=care_provider_type,
            care_provider_name=care_provider_name,
        )

    @property
    def is_active(self) -> bool:
        return self.status is PregnancyStatus.ACTIVE

    def gestational_age_days(self, on: date) -> int:
        return PREGNANCY_LENGTH_DAYS - (self.estimated_due_date - on).days

    def gestational_week(self, on: date) -> int:
        """Completed weeks of pregnancy; derived, not stored, so it never goes stale."""
        return self.gestational_age_days(on) // 7

    def end(self, *, status: PregnancyStatus, on: date) -> None:
        if not self.is_active:
            raise ValidationError("This pregnancy has already ended.")
        if status is PregnancyStatus.ACTIVE:
            raise ValidationError("A pregnancy can only end as delivered or ended.")
        self.status = status
        self.ended_on = on
