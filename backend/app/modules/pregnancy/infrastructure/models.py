"""Section 4: pregnancy path table."""
import uuid
from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.modules.pregnancy.domain.entities import STANDARD_CYCLE_DAYS
from app.modules.pregnancy.domain.enums import CareProviderType, ConceptionType, PregnancyStatus
from app.shared.infrastructure.orm import (
    CreatedAtMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    enum_column,
)


class PregnancyModel(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """A user can have many pregnancies over time, but only one active."""

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
    # Who corrected the due date and when (e.g. after an ultrasound); NULL = from the LMP.
    due_date_corrected_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    due_date_corrected_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id")
    )


class PartnerLinkModel(UUIDPrimaryKeyMixin, CreatedAtMixin, db.Model):
    """The QR code her spouse scans. Only its id is stored: the token is derived from it
    with SECRET_KEY. One active link per mother; turning it off sets ``revoked_at``."""

    __tablename__ = "partner_links"
    __table_args__ = (
        sa.Index(
            "uq_partner_links_one_active_per_user",
            "user_id",
            unique=True,
            postgresql_where=sa.text("revoked_at IS NULL"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
