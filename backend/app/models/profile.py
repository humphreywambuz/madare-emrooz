"""Sections 2, 3 and 9: demographic profile, medical history, fitness profile."""
import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import TimestampMixin, enum_column
from .enums import BloodType, FitnessGoal, JoinGoal, ReproductiveStatus

if TYPE_CHECKING:
    from .user import User


def _user_pk() -> Mapped[uuid.UUID]:
    return mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )


class Profile(TimestampMixin, db.Model):
    """Section 2: base demographic profile (one per user).

    Shared by all paths; the fitness quick sign-up (section 9) fills only name,
    birth date, height and weight.
    """

    __tablename__ = "profiles"
    __table_args__ = (
        sa.CheckConstraint(r"national_code ~ '^[0-9]{10}$'", name="national_code_format"),
        sa.CheckConstraint("height_cm BETWEEN 50 AND 250", name="height_range"),
        sa.CheckConstraint("initial_weight_kg BETWEEN 20 AND 300", name="weight_range"),
    )

    user_id: Mapped[uuid.UUID] = _user_pk()
    first_name: Mapped[str] = mapped_column(sa.String(100))
    last_name: Mapped[str] = mapped_column(sa.String(100))
    national_code: Mapped[str | None] = mapped_column(sa.String(10), unique=True)
    # Birth date instead of a stored age, which would go stale.
    birth_date: Mapped[date | None] = mapped_column(sa.Date)
    height_cm: Mapped[Decimal | None] = mapped_column(sa.Numeric(4, 1))
    initial_weight_kg: Mapped[Decimal | None] = mapped_column(sa.Numeric(5, 2))
    mother_blood_type: Mapped[BloodType | None] = mapped_column(enum_column(BloodType))
    # Father's blood type is kept to detect Rh incompatibility.
    father_blood_type: Mapped[BloodType | None] = mapped_column(enum_column(BloodType))
    reproductive_status: Mapped[ReproductiveStatus | None] = mapped_column(
        enum_column(ReproductiveStatus)
    )
    join_goal: Mapped[JoinGoal] = mapped_column(enum_column(JoinGoal))

    user: Mapped["User"] = relationship(back_populates="profile")

    @property
    def age(self) -> int | None:
        if self.birth_date is None:
            return None
        today = date.today()
        before_birthday = (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        return today.year - self.birth_date.year - before_birthday

    @property
    def rh_incompatibility_risk(self) -> bool:
        """Rh-negative mother with an Rh-positive father (candidate for RhoGAM)."""
        return bool(
            self.mother_blood_type
            and self.father_blood_type
            and self.mother_blood_type.is_rh_negative
            and not self.father_blood_type.is_rh_negative
        )


class MedicalHistory(TimestampMixin, db.Model):
    """Section 3: medical & midwifery history (one per user).

    Yes/no questions are nullable booleans: NULL means "not answered".
    """

    __tablename__ = "medical_histories"
    __table_args__ = (
        sa.CheckConstraint("previous_children_count >= 0", name="children_non_negative"),
        sa.CheckConstraint("miscarriage_count >= 0", name="miscarriages_non_negative"),
    )

    user_id: Mapped[uuid.UUID] = _user_pk()

    previous_children_count: Mapped[int | None] = mapped_column(sa.SmallInteger)
    miscarriage_count: Mapped[int | None] = mapped_column(sa.SmallInteger)

    has_diabetes: Mapped[bool | None]
    has_hypertension: Mapped[bool | None]

    has_nutrient_deficiency: Mapped[bool | None]
    nutrient_deficiency_details: Mapped[str | None] = mapped_column(sa.Text)  # e.g. iron, vit D

    has_thyroid_disorder: Mapped[bool | None]
    has_breast_cyst: Mapped[bool | None]
    has_ovarian_cyst_pcos: Mapped[bool | None]

    # Structural / organic conditions, e.g. herniated disc, heart disease.
    underlying_conditions: Mapped[str | None] = mapped_column(sa.Text)

    has_previous_surgery: Mapped[bool | None]
    previous_surgery_details: Mapped[str | None] = mapped_column(sa.Text)
    has_anesthesia_history: Mapped[bool | None]

    current_medications: Mapped[str | None] = mapped_column(sa.Text)

    has_dental_infection: Mapped[bool | None]  # gum / tooth infections
    dental_notes: Mapped[str | None] = mapped_column(sa.Text)

    has_hiv: Mapped[bool | None]
    has_hepatitis_b: Mapped[bool | None]
    has_hepatitis_c: Mapped[bool | None]
    other_infectious_diseases: Mapped[str | None] = mapped_column(sa.Text)

    spouse_has_diabetes: Mapped[bool | None]
    spouse_has_varicocele: Mapped[bool | None]
    spouse_has_genetic_disorder: Mapped[bool | None]
    spouse_health_notes: Mapped[str | None] = mapped_column(sa.Text)

    user: Mapped["User"] = relationship(back_populates="medical_history")


class FitnessProfile(TimestampMixin, db.Model):
    """Section 9: fitness & daily sport path (option B).

    Identity fields (name, mobile, age, height, weight) live on User/Profile.
    """

    __tablename__ = "fitness_profiles"

    user_id: Mapped[uuid.UUID] = _user_pk()
    goal: Mapped[FitnessGoal] = mapped_column(enum_column(FitnessGoal))
    goal_note: Mapped[str | None] = mapped_column(sa.Text)

    user: Mapped["User"] = relationship(back_populates="fitness_profile")
