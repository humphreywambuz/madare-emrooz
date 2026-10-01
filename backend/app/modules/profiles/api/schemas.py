from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.profiles.domain.enums import BloodType, JoinGoal, ReproductiveStatus


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProfileBody(_Body):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    join_goal: JoinGoal
    national_code: str | None = Field(default=None, max_length=10)
    birth_date: date | None = None
    height_cm: Decimal | None = Field(default=None, ge=50, le=250, decimal_places=1)
    initial_weight_kg: Decimal | None = Field(default=None, ge=20, le=300, decimal_places=2)
    mother_blood_type: BloodType | None = None
    spouse_blood_type: BloodType | None = None
    reproductive_status: ReproductiveStatus | None = None


_text = Field(default=None, max_length=2000)


class MedicalHistoryBody(_Body):
    previous_children_count: int | None = Field(default=None, ge=0, le=30)
    miscarriage_count: int | None = Field(default=None, ge=0, le=30)
    has_diabetes: bool | None = None
    has_hypertension: bool | None = None
    has_nutrient_deficiency: bool | None = None
    nutrient_deficiency_details: str | None = _text
    has_thyroid_disorder: bool | None = None
    has_breast_cyst: bool | None = None
    has_ovarian_cyst_pcos: bool | None = None
    underlying_conditions: str | None = _text
    has_previous_surgery: bool | None = None
    previous_surgery_details: str | None = _text
    has_anesthesia_history: bool | None = None
    current_medications: str | None = _text
    has_dental_infection: bool | None = None
    dental_notes: str | None = _text
    has_hiv: bool | None = None
    has_hepatitis_b: bool | None = None
    has_hepatitis_c: bool | None = None
    other_infectious_diseases: str | None = _text
    spouse_has_diabetes: bool | None = None
    spouse_has_varicocele: bool | None = None
    spouse_has_genetic_disorder: bool | None = None
    spouse_health_notes: str | None = _text
