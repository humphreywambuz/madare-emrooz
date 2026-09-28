"""Section 1: User auth & role model."""
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin, enum_column
from .enums import UserRole

if TYPE_CHECKING:
    from .pregnancy import Pregnancy
    from .profile import FitnessProfile, MedicalHistory, Profile
    from .rehab import RehabProfile
    from .staff import CareApproval, RiskTagAssignment


class User(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = (
        # E.164 format, e.g. +989121234567
        sa.CheckConstraint(r"mobile ~ '^\+[1-9][0-9]{7,14}$'", name="mobile_e164"),
    )

    mobile: Mapped[str] = mapped_column(sa.String(16), unique=True)
    role: Mapped[UserRole] = mapped_column(
        enum_column(UserRole), default=UserRole.USER, server_default=UserRole.USER.value
    )
    is_active: Mapped[bool] = mapped_column(default=True, server_default=sa.true())
    mobile_verified_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))

    profile: Mapped["Profile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    medical_history: Mapped["MedicalHistory | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    fitness_profile: Mapped["FitnessProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    rehab_profile: Mapped["RehabProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    pregnancies: Mapped[list["Pregnancy"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    risk_tags: Mapped[list["RiskTagAssignment"]] = relationship(
        foreign_keys="RiskTagAssignment.patient_id",
        back_populates="patient",
        cascade="all, delete-orphan",
    )
    care_approvals: Mapped[list["CareApproval"]] = relationship(
        foreign_keys="CareApproval.patient_id",
        back_populates="patient",
        cascade="all, delete-orphan",
    )

    @property
    def is_staff(self) -> bool:
        return self.role in (UserRole.DOCTOR, UserRole.MIDWIFE, UserRole.ADMIN)

    def has_active_approval(self, scope) -> bool:
        return any(a.scope == scope and a.is_active for a in self.care_approvals)

    def __repr__(self) -> str:
        return f"<User {self.mobile} ({self.role})>"


class OtpCode(UUIDPrimaryKeyMixin, CreatedAtMixin, db.Model):
    """One-time login code. Keyed by mobile because the user may not exist yet.

    Only a hash of the code is stored, never the plain code.
    """

    __tablename__ = "otp_codes"
    __table_args__ = (
        sa.Index("ix_otp_codes_mobile_created_at", "mobile", "created_at"),
        sa.CheckConstraint("attempts >= 0", name="attempts_non_negative"),
    )

    mobile: Mapped[str] = mapped_column(sa.String(16))
    code_hash: Mapped[str] = mapped_column(sa.String(255))
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(sa.SmallInteger, default=0, server_default="0")
    consumed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))

    @property
    def is_usable(self) -> bool:
        return self.consumed_at is None and self.expires_at > datetime.now(timezone.utc)


class UserSession(UUIDPrimaryKeyMixin, CreatedAtMixin, db.Model):
    """A logged-in device. Stores a hash of the refresh token."""

    __tablename__ = "user_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    refresh_token_hash: Mapped[str] = mapped_column(sa.String(255), unique=True)
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(sa.Text)
    last_seen_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="sessions")

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None and self.expires_at > datetime.now(timezone.utc)
