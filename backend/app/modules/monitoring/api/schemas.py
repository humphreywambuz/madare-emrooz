from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BleedingReportBody(_Body):
    """All the mother can record herself; anything else is rejected."""

    has_spotting_or_bleeding: bool


class MidwifeLogBody(_Body):
    has_spotting_or_bleeding: bool | None = None
    systolic_bp: int | None = Field(default=None, ge=50, le=260)
    diastolic_bp: int | None = Field(default=None, ge=30, le=160)
    blood_glucose_mg_dl: int | None = Field(default=None, ge=20, le=600)
    weight_kg: Decimal | None = Field(default=None, ge=20, le=300, decimal_places=2)
    has_acid_reflux: bool | None = None
    has_blurred_vision: bool | None = None
    has_headache: bool | None = None
    has_palpitations: bool | None = None
    has_heartburn: bool | None = None
    has_reduced_fetal_movement: bool | None = None
    other_complaints: str | None = Field(default=None, max_length=2000)
