"""Rehabilitation initial health profile (spec sections 10 and 11). Pure Python."""
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.shared.domain.errors import ValidationError

from .enums import (
    FitnessLevel,
    InjuryOnset,
    OrthopedicReferralReason,
    PainType,
    RehabSubcategory,
    TimeSinceDelivery,
    TrainingGoal,
)

_PERFORMANCE = ("training_goal", "fitness_level", "has_recurrent_muscle_spasms")

# The extra questions asked for each sub-type; the others must stay empty.
SUBCATEGORY_QUESTIONS: dict[RehabSubcategory, tuple[str, ...]] = {
    RehabSubcategory.INJURY_CORRECTION: ("injury_onset", "pain_type", "has_daily_movement_limitation"),
    RehabSubcategory.POSTPARTUM_RECOVERY: (
        "time_since_delivery", "has_pelvic_warning_signs", "has_diastasis_recti_or_stitch_pain",
    ),
    RehabSubcategory.PERFORMANCE_IMPROVEMENT: _PERFORMANCE,
    RehabSubcategory.YOGA_MEDITATION: _PERFORMANCE,
    RehabSubcategory.ORTHOPEDIC_REFERRAL: ("referral_reason",),
}
ALL_SUBCATEGORY_QUESTIONS = frozenset(q for qs in SUBCATEGORY_QUESTIONS.values() for q in qs)
COMMON_QUESTIONS = (
    "subcategory", "pain_level", "had_related_surgery", "related_surgery_name", "uses_pain_medication",
)


@dataclass
class RehabProfile:
    user_id: uuid.UUID
    subcategory: RehabSubcategory
    pain_level: int  # 1..10
    had_related_surgery: bool
    uses_pain_medication: bool
    related_surgery_name: str | None = None
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
    # X-ray / MRI uploaded by her midwife (a medical_documents row).
    imaging_document_id: uuid.UUID | None = None
    specialist_visit_completed: bool = False
    specialist_visit_at: datetime | None = None

    def answer(self, answers: dict[str, Any]) -> None:
        """Replace her questionnaire answers; the visit and imaging set by staff are kept."""
        unknown = set(answers) - set(COMMON_QUESTIONS) - ALL_SUBCATEGORY_QUESTIONS
        if unknown:
            raise ValidationError(f"Unknown questions: {', '.join(sorted(unknown))}.")
        for name in (*COMMON_QUESTIONS, *ALL_SUBCATEGORY_QUESTIONS):
            setattr(self, name, answers.get(name))
        self.validate()

    def validate(self) -> None:
        if not 1 <= self.pain_level <= 10:
            raise ValidationError("Pain level is from 1 to 10.", details={"field": "pain_level"})
        if self.had_related_surgery and not (self.related_surgery_name or "").strip():
            raise ValidationError(
                "Name the surgery.", details={"field": "related_surgery_name"}
            )
        if not self.had_related_surgery:
            self.related_surgery_name = None
        other = ALL_SUBCATEGORY_QUESTIONS - set(SUBCATEGORY_QUESTIONS[self.subcategory])
        answered = sorted(name for name in other if getattr(self, name) is not None)
        if answered:
            raise ValidationError(
                "These questions belong to another sub-type.", details={"fields": answered}
            )

    def record_specialist_visit(self, at: datetime) -> None:
        self.specialist_visit_completed = True
        self.specialist_visit_at = at

    @classmethod
    def from_answers(cls, user_id: uuid.UUID, answers: dict[str, Any]) -> "RehabProfile":
        profile = cls(
            user_id=user_id,
            subcategory=answers["subcategory"],
            pain_level=answers["pain_level"],
            had_related_surgery=answers["had_related_surgery"],
            uses_pain_medication=answers["uses_pain_medication"],
        )
        profile.answer(answers)
        return profile
