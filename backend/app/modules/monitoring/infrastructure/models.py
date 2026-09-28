"""Section 5: daily monitoring & symptoms table."""
import uuid
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.shared.infrastructure.orm import TimestampMixin, UUIDPrimaryKeyMixin


class DailyLogModel(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """Entries can be recorded by the patient (e.g. bleeding) or by a midwife
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
