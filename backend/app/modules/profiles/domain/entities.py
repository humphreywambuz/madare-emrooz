"""Profile aggregates (spec sections 2 and 3). Pure Python: no Flask, no SQLAlchemy."""
import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.modules.identity.domain.mobile import to_ascii_digits
from app.shared.domain.errors import ValidationError

from .enums import BloodType, HomePath, JoinGoal, ReproductiveStatus
from .rules import is_valid_national_code, rh_incompatibility_risk

_HOME_FOR_STATUS = {
    ReproductiveStatus.PREGNANT: HomePath.PREGNANCY,
    ReproductiveStatus.TRYING_TO_CONCEIVE: HomePath.TRYING_TO_CONCEIVE,
    ReproductiveStatus.POSTPARTUM: HomePath.POSTPARTUM,
}


@dataclass
class Profile:
    user_id: uuid.UUID
    first_name: str
    last_name: str
    join_goal: JoinGoal
    national_code: str | None = None
    birth_date: date | None = None
    height_cm: Decimal | None = None
    initial_weight_kg: Decimal | None = None
    mother_blood_type: BloodType | None = None
    # The spouse's blood type, asked in the pregnant mother's profile.
    father_blood_type: BloodType | None = None
    reproductive_status: ReproductiveStatus | None = None

    def validate(self, today: date) -> None:
        """Rules checked whenever the mother saves her profile."""
        self.first_name, self.last_name = self.first_name.strip(), self.last_name.strip()
        if not self.first_name or not self.last_name:
            raise ValidationError("First and last name are required.", details={"field": "first_name"})
        if self.national_code is not None:
            self.national_code = to_ascii_digits(self.national_code).strip()
            if not is_valid_national_code(self.national_code):
                raise ValidationError(
                    "This national code is not valid.", details={"field": "national_code"}
                )
        if self.birth_date is not None and self.birth_date >= today:
            raise ValidationError("Birth date must be in the past.", details={"field": "birth_date"})
        if self.join_goal is JoinGoal.PREGNANCY and self.reproductive_status is None:
            raise ValidationError(
                "Choose whether you are trying to conceive, pregnant or have given birth.",
                details={"field": "reproductive_status"},
            )

    @property
    def home(self) -> HomePath:
        if self.join_goal is JoinGoal.PREGNANCY:
            return _HOME_FOR_STATUS[self.reproductive_status]
        return HomePath(self.join_goal.value)

    @property
    def rh_incompatibility_risk(self) -> bool:
        return rh_incompatibility_risk(self.mother_blood_type, self.father_blood_type)

    def record_delivery(self) -> None:
        """After the birth her home becomes the postpartum one (fitness and rehabilitation)."""
        if self.join_goal is JoinGoal.PREGNANCY:
            self.reproductive_status = ReproductiveStatus.POSTPARTUM


@dataclass
class MedicalHistory:
    """Every answer is optional: None means "not answered", which is different from "no"."""

    user_id: uuid.UUID
    previous_children_count: int | None = None
    miscarriage_count: int | None = None
    has_diabetes: bool | None = None
    has_hypertension: bool | None = None
    has_nutrient_deficiency: bool | None = None
    nutrient_deficiency_details: str | None = None
    has_thyroid_disorder: bool | None = None
    has_breast_cyst: bool | None = None
    has_ovarian_cyst_pcos: bool | None = None
    underlying_conditions: str | None = None
    has_previous_surgery: bool | None = None
    previous_surgery_details: str | None = None
    has_anesthesia_history: bool | None = None
    current_medications: str | None = None
    has_dental_infection: bool | None = None
    dental_notes: str | None = None
    has_hiv: bool | None = None
    has_hepatitis_b: bool | None = None
    has_hepatitis_c: bool | None = None
    other_infectious_diseases: str | None = None
    spouse_has_diabetes: bool | None = None
    spouse_has_varicocele: bool | None = None
    spouse_has_genetic_disorder: bool | None = None
    spouse_health_notes: str | None = None
