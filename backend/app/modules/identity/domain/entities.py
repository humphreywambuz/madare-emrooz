"""Identity aggregates (spec section 1). Pure Python: no Flask, no SQLAlchemy."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from .enums import UserRole


@dataclass
class User:
    mobile: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    mobile_verified_at: datetime | None = None
    last_login_at: datetime | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def record_login(self, now: datetime) -> None:
        if self.mobile_verified_at is None:
            self.mobile_verified_at = now
        self.last_login_at = now


@dataclass
class OtpChallenge:
    """A code sent by SMS. Only the latest challenge for a mobile number counts."""

    mobile: str
    code_hash: str
    created_at: datetime
    expires_at: datetime
    request_ip: str | None = None
    attempts: int = 0
    consumed_at: datetime | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def is_expired(self, now: datetime) -> bool:
        return now >= self.expires_at

    def attempts_left(self, max_attempts: int) -> int:
        return max(max_attempts - self.attempts, 0)

    def register_failed_attempt(self) -> None:
        self.attempts += 1

    def consume(self, now: datetime) -> None:
        self.consumed_at = now


@dataclass
class Session:
    """A signed-in device, identified by the hash of its current refresh token.

    Each renewal replaces the token and counts up ``refresh_generation``; the token is
    signed with its generation, so an older one can be told apart from a forged one.
    """

    user_id: uuid.UUID
    refresh_token_hash: str
    created_at: datetime
    expires_at: datetime
    ip_address: str | None = None
    user_agent: str | None = None
    last_seen_at: datetime | None = None
    revoked_at: datetime | None = None
    refresh_generation: int = 0
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def is_active(self, now: datetime) -> bool:
        return self.revoked_at is None and now < self.expires_at

    def rotate(self, new_refresh_token_hash: str, now: datetime) -> None:
        """Replace the refresh token, made for ``refresh_generation + 1``, so each one is used once."""
        self.refresh_token_hash = new_refresh_token_hash
        self.refresh_generation += 1
        self.last_seen_at = now

    def revoke(self, now: datetime) -> None:
        if self.revoked_at is None:
            self.revoked_at = now
