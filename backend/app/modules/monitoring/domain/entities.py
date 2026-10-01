"""Daily monitoring (spec section 5). Pure Python: no Flask, no SQLAlchemy."""
import uuid
from dataclasses import dataclass, field, fields
from datetime import datetime
from decimal import Decimal

from app.shared.domain.errors import ValidationError

# What the midwife records. The mother only reports spotting or bleeding.
MEASUREMENTS = (
    "systolic_bp", "diastolic_bp", "blood_glucose_mg_dl", "weight_kg",
    "has_acid_reflux", "has_blurred_vision", "has_headache", "has_palpitations",
    "has_heartburn", "has_reduced_fetal_movement", "other_complaints",
)


@dataclass
class DailyLog:
    patient_id: uuid.UUID
    recorded_by_id: uuid.UUID
    recorded_at: datetime
    pregnancy_id: uuid.UUID | None = None
    has_spotting_or_bleeding: bool | None = None
    systolic_bp: int | None = None
    diastolic_bp: int | None = None
    blood_glucose_mg_dl: int | None = None
    weight_kg: Decimal | None = None
    has_acid_reflux: bool | None = None
    has_blurred_vision: bool | None = None
    has_headache: bool | None = None
    has_palpitations: bool | None = None
    has_heartburn: bool | None = None
    has_reduced_fetal_movement: bool | None = None
    other_complaints: str | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    @property
    def is_red_alert(self) -> bool:
        """Same rule as the generated column daily_logs.is_red_alert."""
        return bool(self.has_spotting_or_bleeding)

    def validate(self) -> None:
        if self.has_spotting_or_bleeding is None and all(
            getattr(self, name) is None for name in MEASUREMENTS
        ):
            raise ValidationError("Record at least one value.")
        if (self.systolic_bp is None) != (self.diastolic_bp is None):
            raise ValidationError(
                "Blood pressure needs both numbers.", details={"field": "diastolic_bp"}
            )
        if self.systolic_bp is not None and self.systolic_bp <= self.diastolic_bp:
            raise ValidationError(
                "Systolic pressure must be higher than diastolic.", details={"field": "systolic_bp"}
            )


DAILY_LOG_FIELDS = tuple(f.name for f in fields(DailyLog))
