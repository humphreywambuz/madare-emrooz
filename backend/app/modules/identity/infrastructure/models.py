"""Section 1: user auth & role tables."""
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.modules.identity.domain.enums import STAFF_ROLES, UserRole
from app.shared.infrastructure.orm import (
    CreatedAtMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    enum_column,
)


class UserModel(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
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

    sessions: Mapped[list["UserSessionModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def is_staff(self) -> bool:
        return self.role in STAFF_ROLES

    def __repr__(self) -> str:
        return f"<User {self.mobile} ({self.role})>"


class OtpCodeModel(UUIDPrimaryKeyMixin, CreatedAtMixin, db.Model):
    """One-time login code. Keyed by mobile because the user may not exist yet.

    Only a hash of the code is stored, never the plain code.
    """

    __tablename__ = "otp_codes"
    __table_args__ = (
        sa.Index("ix_otp_codes_mobile_created_at", "mobile", "created_at"),
        sa.Index("ix_otp_codes_request_ip_created_at", "request_ip", "created_at"),
        sa.CheckConstraint("attempts >= 0", name="attempts_non_negative"),
    )

    mobile: Mapped[str] = mapped_column(sa.String(16))
    # Used to limit how many codes one network can request (SMS abuse).
    request_ip: Mapped[str | None] = mapped_column(INET)
    code_hash: Mapped[str] = mapped_column(sa.String(255))
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(sa.SmallInteger, default=0, server_default="0")
    consumed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class UserSessionModel(UUIDPrimaryKeyMixin, CreatedAtMixin, db.Model):
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

    user: Mapped[UserModel] = relationship(back_populates="sessions")
