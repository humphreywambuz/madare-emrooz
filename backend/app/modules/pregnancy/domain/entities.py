"""Pregnancy aggregate (spec section 4). Pure Python: no Flask, no SQLAlchemy."""
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

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
    # Set when a clinician corrects the due date (e.g. from an ultrasound). From then on the
    # due date no longer follows the LMP.
    due_date_corrected_at: datetime | None = None
    due_date_corrected_by_id: uuid.UUID | None = None
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
        _check_lmp(lmp_date, avg_cycle_length_days, today)
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

    @property
    def due_date_source(self) -> str:
        """"lmp": calculated from her last period; "clinician": corrected by her care team."""
        return "clinician" if self.due_date_corrected_at else "lmp"

    def correct_details(self, today: date, **changes) -> None:
        """The mother fixes what she entered (LMP, cycle length, conception, care provider).

        The due date is recalculated from the LMP unless a clinician has already corrected it.
        """
        self._require_active()
        unknown = set(changes) - {
            "lmp_date", "avg_cycle_length_days", "conception_type",
            "care_provider_type", "care_provider_name",
        }
        if unknown:
            raise ValidationError(f"These fields can't be changed: {', '.join(sorted(unknown))}.")
        lmp = changes.get("lmp_date", self.lmp_date)
        cycle = changes.get("avg_cycle_length_days", self.avg_cycle_length_days)
        _check_lmp(lmp, cycle, today)
        for name, value in changes.items():
            setattr(self, name, value)
        if self.due_date_source == "lmp":
            self.estimated_due_date = calculate_due_date(lmp, cycle)

    def correct_due_date(self, due_date: date, *, by: uuid.UUID, at: datetime, today: date) -> None:
        """A clinician sets the due date, e.g. from an ultrasound."""
        self._require_active()
        age_days = PREGNANCY_LENGTH_DAYS - (due_date - today).days
        if not 0 <= age_days <= MAX_PREGNANCY_DAYS:
            raise ValidationError(
                "This due date doesn't fit an ongoing pregnancy.",
                details={"field": "estimated_due_date"},
            )
        self.estimated_due_date = due_date
        self.due_date_corrected_at = at
        self.due_date_corrected_by_id = by

    def _require_active(self) -> None:
        if not self.is_active:
            raise ValidationError("This pregnancy has already ended.")

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


def _check_lmp(lmp_date: date, cycle_length_days: int, today: date) -> None:
    if lmp_date > today:
        raise ValidationError("The last menstrual period cannot be in the future.")
    if (today - lmp_date).days > MAX_PREGNANCY_DAYS:
        raise ValidationError("The last menstrual period is too long ago for an ongoing pregnancy.")
    if not MIN_CYCLE_DAYS <= cycle_length_days <= MAX_CYCLE_DAYS:
        raise ValidationError(
            f"Cycle length must be between {MIN_CYCLE_DAYS} and {MAX_CYCLE_DAYS} days."
        )
