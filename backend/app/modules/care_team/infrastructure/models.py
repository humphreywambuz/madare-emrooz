"""Section 7: medical staff panel (staff profiles, assignments, alerts, summary-card tags,
notes, approvals)."""
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.modules.care_team.domain.enums import AlertKind, ApprovalScope, CareRole, RiskTag
from app.shared.infrastructure.orm import (
    CreatedAtMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    enum_column,
)


class RiskTagAssignmentModel(UUIDPrimaryKeyMixin, CreatedAtMixin, db.Model):
    """A risk tag shown on the patient's summary card (e.g. needs RhoGAM)."""

    __tablename__ = "risk_tag_assignments"
    __table_args__ = (sa.UniqueConstraint("patient_id", "tag", name="uq_risk_tag_per_patient"),)

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    tag: Mapped[RiskTag] = mapped_column(enum_column(RiskTag))
    note: Mapped[str | None] = mapped_column(sa.String(255))
    added_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("users.id"))


class StaffNoteModel(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """Free-text opinion / intervention recorded by a doctor or midwife."""

    __tablename__ = "staff_notes"
    __table_args__ = (sa.Index("ix_staff_notes_patient_created_at", "patient_id", "created_at"),)

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")
    )
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(sa.Text)


class CareApprovalModel(UUIDPrimaryKeyMixin, CreatedAtMixin, db.Model):
    """Doctor's approval checkmark that unlocks a patient's care/training plan.

    Used for both the pregnancy plan (section 7) and rehabilitation (section 11).
    Revoking sets ``revoked_at`` rather than deleting, to keep history.
    Only doctors may approve; that is enforced in the service layer.
    """

    __tablename__ = "care_approvals"
    __table_args__ = (
        sa.Index(
            "uq_care_approvals_one_active_per_scope",
            "patient_id",
            "scope",
            unique=True,
            postgresql_where=sa.text("revoked_at IS NULL"),
        ),
    )

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")
    )
    approved_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id")
    )
    scope: Mapped[ApprovalScope] = mapped_column(enum_column(ApprovalScope))
    approved_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    revoked_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id")
    )

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None


class StaffProfileModel(TimestampMixin, db.Model):
    """Name and bio of a doctor, midwife or admin. The account (mobile, role) is in ``users``."""

    __tablename__ = "staff_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    first_name: Mapped[str] = mapped_column(sa.String(100))
    last_name: Mapped[str] = mapped_column(sa.String(100))
    bio: Mapped[str | None] = mapped_column(sa.Text)
    # Listed midwives appear in the app for mothers to choose from.
    is_listed: Mapped[bool] = mapped_column(default=True, server_default=sa.true())


class CareAssignmentModel(UUIDPrimaryKeyMixin, CreatedAtMixin, db.Model):
    """The staff member a mother chose for a role: her midwife now, her doctor in Phase 2.

    Changing midwife ends the old row (``ended_at``) so the history is kept; a partial
    unique index allows one active assignment per mother and role.
    """

    __tablename__ = "care_assignments"
    __table_args__ = (
        sa.Index(
            "uq_care_assignments_one_active_per_role",
            "patient_id",
            "care_role",
            unique=True,
            postgresql_where=sa.text("ended_at IS NULL"),
        ),
        sa.Index(
            "ix_care_assignments_active_staff",
            "staff_id",
            "care_role",
            postgresql_where=sa.text("ended_at IS NULL"),
        ),
    )

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")
    )
    staff_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("users.id"))
    care_role: Mapped[CareRole] = mapped_column(enum_column(CareRole))
    started_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class AlertModel(UUIDPrimaryKeyMixin, CreatedAtMixin, db.Model):
    """A red alert, e.g. the mother reported bleeding. It is shown to her midwife, or to
    the admins while she has none, until someone marks it as seen."""

    __tablename__ = "alerts"
    __table_args__ = (
        sa.Index("ix_alerts_open", "patient_id", postgresql_where=sa.text("seen_at IS NULL")),
    )

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")
    )
    kind: Mapped[AlertKind] = mapped_column(enum_column(AlertKind))
    daily_log_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("daily_logs.id", ondelete="CASCADE")
    )
    seen_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    seen_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id")
    )
