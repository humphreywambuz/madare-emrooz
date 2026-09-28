"""Sections 4 and 5: pregnancy path and daily monitoring."""
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import TimestampMixin, UUIDPrimaryKeyMixin, enum_column
from .enums import CareProviderType, ConceptionType, PregnancyStatus

if TYPE_CHECKING:
    from .user import User

PREGNANCY_LENGTH_DAYS = 280
STANDARD_CYCLE_DAYS = 28


class Pregnancy(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """Section 4: a pregnancy. A user can have many over time, but only one active."""

    __tablename__ = "pregnancies"
    __table_args__ = (
        sa.CheckConstraint("avg_cycle_length_days BETWEEN 20 AND 45", name="cycle_length_range"),
        sa.Index(
            "uq_pregnancies_one_active_per_user",
            "user_id",
            unique=True,
            postgresql_where=sa.text("status = 'active'"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    lmp_date: Mapped[date] = mapped_column(sa.Date)  # first day of last menstrual period
    avg_cycle_length_days: Mapped[int] = mapped_column(
        sa.SmallInteger, default=STANDARD_CYCLE_DAYS, server_default=str(STANDARD_CYCLE_DAYS)
    )
    conception_type: Mapped[ConceptionType] = mapped_column(enum_column(ConceptionType))
    # Calculated from LMP on creation; clinicians may correct it (e.g. from ultrasound).
    estimated_due_date: Mapped[date] = mapped_column(sa.Date)
    care_provider_type: Mapped[CareProviderType | None] = mapped_column(
        enum_column(CareProviderType)
    )
    care_provider_name: Mapped[str | None] = mapped_column(sa.String(200))
    status: Mapped[PregnancyStatus] = mapped_column(
        enum_column(PregnancyStatus),
        default=PregnancyStatus.ACTIVE,
        server_default=PregnancyStatus.ACTIVE.value,
    )
    ended_on: Mapped[date | None] = mapped_column(sa.Date)

    user: Mapped["User"] = relationship(back_populates="pregnancies")
    daily_logs: Mapped[list["DailyLog"]] = relationship(back_populates="pregnancy")

    @staticmethod
    def calculate_due_date(lmp_date: date, cycle_length_days: int = STANDARD_CYCLE_DAYS) -> date:
        """Naegele's rule, adjusted for cycle length."""
        return lmp_date + timedelta(
            days=PREGNANCY_LENGTH_DAYS + (cycle_length_days - STANDARD_CYCLE_DAYS)
        )

    def gestational_age_days(self, on: date | None = None) -> int:
        on = on or date.today()
        return PREGNANCY_LENGTH_DAYS - (self.estimated_due_date - on).days

    def gestational_week(self, on: date | None = None) -> int:
        """Completed weeks of pregnancy; derived, not stored, so it never goes stale."""
        return self.gestational_age_days(on) // 7


class DailyLog(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """Section 5: daily monitoring & symptoms.

    Entries can be recorded by the patient (e.g. bleeding) or by a midwife
    (vitals, weight, symptoms); ``recorded_by_id`` says who.
    """

    __tablename__ = "daily_logs"
    __table_args__ = (
        sa.CheckConstraint("systolic_bp BETWEEN 50 AND 260", name="systolic_range"),
        sa.CheckConstraint("diastolic_bp BETWEEN 30 AND 160", name="diastolic_range"),
        sa.CheckConstraint("blood_glucose_mg_dl BETWEEN 20 AND 600", name="glucose_range"),
        sa.CheckConstraint("weight_kg BETWEEN 20 AND 300", name="weight_range"),
        sa.Index("ix_daily_logs_patient_recorded_at", "patient_id", sa.text("recorded_at DESC")),
        sa.Index(
            "ix_daily_logs_red_alerts",
            "patient_id",
            postgresql_where=sa.text("is_red_alert"),
        ),
    )

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")
    )
    pregnancy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("pregnancies.id", ondelete="SET NULL"), index=True
    )
    recorded_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id")
    )
    recorded_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )

    has_spotting_or_bleeding: Mapped[bool | None]
    systolic_bp: Mapped[int | None] = mapped_column(sa.SmallInteger)
    diastolic_bp: Mapped[int | None] = mapped_column(sa.SmallInteger)
    blood_glucose_mg_dl: Mapped[int | None] = mapped_column(sa.SmallInteger)
    weight_kg: Mapped[Decimal | None] = mapped_column(sa.Numeric(5, 2))

    has_acid_reflux: Mapped[bool | None]
    has_blurred_vision: Mapped[bool | None]
    has_headache: Mapped[bool | None]
    has_palpitations: Mapped[bool | None]
    has_heartburn: Mapped[bool | None]
    has_reduced_fetal_movement: Mapped[bool | None]
    other_complaints: Mapped[str | None] = mapped_column(sa.Text)

    # Computed by PostgreSQL so it can never disagree with the underlying data.
    is_red_alert: Mapped[bool] = mapped_column(
        sa.Computed("COALESCE(has_spotting_or_bleeding, false)", persisted=True)
    )

    patient: Mapped["User"] = relationship(foreign_keys=[patient_id])
    recorded_by: Mapped["User"] = relationship(foreign_keys=[recorded_by_id])
    pregnancy: Mapped[Pregnancy | None] = relationship(back_populates="daily_logs")
