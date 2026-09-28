"""Sections 10 and 11: rehabilitation initial health profile and access control."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import TimestampMixin, enum_column
from .enums import (
    ApprovalScope,
    FitnessLevel,
    InjuryOnset,
    OrthopedicReferralReason,
    PainType,
    RehabSubcategory,
    TimeSinceDelivery,
    TrainingGoal,
)

if TYPE_CHECKING:
    from .document import MedicalDocument
    from .user import User


class RehabProfile(TimestampMixin, db.Model):
    """Initial health profile for the rehabilitation path (option C), one per user.

    Common fields apply to every sub-category; the sub-category specific fields
    are nullable and only filled for the chosen sub-category.
    """

    __tablename__ = "rehab_profiles"
    __table_args__ = (
        sa.CheckConstraint("pain_level BETWEEN 1 AND 10", name="pain_level_range"),
        sa.CheckConstraint(
            "had_related_surgery IS NOT TRUE OR related_surgery_name IS NOT NULL",
            name="surgery_name_required",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )

    # --- a) Common fields -------------------------------------------------
    subcategory: Mapped[RehabSubcategory] = mapped_column(enum_column(RehabSubcategory))
    pain_level: Mapped[int] = mapped_column(sa.SmallInteger)  # slider 1..10
    # Joint, bone or childbirth-related surgery in the last 5 years.
    had_related_surgery: Mapped[bool]
    related_surgery_name: Mapped[str | None] = mapped_column(sa.String(255))
    uses_pain_medication: Mapped[bool]  # painkillers, anti-inflammatories, etc.

    # --- b) Injury correction ----------------------------------------------
    injury_onset: Mapped[InjuryOnset | None] = mapped_column(enum_column(InjuryOnset))
    pain_type: Mapped[PainType | None] = mapped_column(enum_column(PainType))
    has_daily_movement_limitation: Mapped[bool | None]

    # --- b) Postpartum recovery --------------------------------------------
    time_since_delivery: Mapped[TimeSinceDelivery | None] = mapped_column(
        enum_column(TimeSinceDelivery)
    )
    has_pelvic_warning_signs: Mapped[bool | None]  # incontinence, prolapse
    has_diastasis_recti_or_stitch_pain: Mapped[bool | None]

    # --- b) Performance improvement / yoga ---------------------------------
    training_goal: Mapped[TrainingGoal | None] = mapped_column(enum_column(TrainingGoal))
    fitness_level: Mapped[FitnessLevel | None] = mapped_column(enum_column(FitnessLevel))
    has_recurrent_muscle_spasms: Mapped[bool | None]  # neck, shoulder or back

    # --- b) Orthopedic referral --------------------------------------------
    referral_reason: Mapped[OrthopedicReferralReason | None] = mapped_column(
        enum_column(OrthopedicReferralReason)
    )
    imaging_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("medical_documents.id", ondelete="SET NULL")
    )

    # --- Section 11: access control (hidden system fields) -----------------
    specialist_visit_completed: Mapped[bool] = mapped_column(
        default=False, server_default=sa.false()
    )
    specialist_visit_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="rehab_profile")
    imaging_document: Mapped["MedicalDocument | None"] = relationship()

    @property
    def is_advanced_locked(self) -> bool:
        """Advanced exercises stay locked until a specialist visit has taken
        place and a doctor has approved the rehabilitation plan."""
        return not (
            self.specialist_visit_completed
            and self.user.has_active_approval(ApprovalScope.REHABILITATION_PLAN)
        )
