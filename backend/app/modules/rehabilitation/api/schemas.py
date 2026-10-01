import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.modules.rehabilitation.domain.enums import (
    FitnessLevel,
    InjuryOnset,
    OrthopedicReferralReason,
    PainType,
    RehabSubcategory,
    TimeSinceDelivery,
    TrainingGoal,
)


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RehabBody(_Body):
    """The questionnaire. Only the questions of the chosen sub-type may be answered."""

    subcategory: RehabSubcategory
    pain_level: int = Field(ge=1, le=10)
    had_related_surgery: bool
    related_surgery_name: str | None = Field(default=None, max_length=255)
    uses_pain_medication: bool
    injury_onset: InjuryOnset | None = None
    pain_type: PainType | None = None
    has_daily_movement_limitation: bool | None = None
    time_since_delivery: TimeSinceDelivery | None = None
    has_pelvic_warning_signs: bool | None = None
    has_diastasis_recti_or_stitch_pain: bool | None = None
    training_goal: TrainingGoal | None = None
    fitness_level: FitnessLevel | None = None
    has_recurrent_muscle_spasms: bool | None = None
    referral_reason: OrthopedicReferralReason | None = None


class ImagingBody(_Body):
    document_id: uuid.UUID
