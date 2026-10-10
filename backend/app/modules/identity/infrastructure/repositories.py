"""SQLAlchemy implementations of the identity ports. Each maps rows to domain entities."""
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Session as OrmSession

from app.modules.identity.domain.entities import OtpChallenge, Session, User

from .models import OtpCodeModel, UserModel, UserSessionModel

_USER_FIELDS = ("id", "mobile", "role", "is_active", "mobile_verified_at", "last_login_at")
_OTP_FIELDS = (
    "id", "mobile", "code_hash", "created_at", "expires_at", "request_ip", "attempts", "consumed_at",
)
_SESSION_FIELDS = (
    "id", "user_id", "refresh_token_hash", "created_at", "expires_at", "ip_address",
    "user_agent", "last_seen_at", "revoked_at", "refresh_generation",
)


def _copy(source, target, fields) -> None:
    for f in fields:
        setattr(target, f, getattr(source, f))


def _ip(value) -> str | None:
    # psycopg returns INET values as ipaddress objects.
    return str(value) if value is not None else None


class SqlAlchemyUserRepository:
    def __init__(self, session: OrmSession):
        self._session = session

    def _to_entity(self, row: UserModel) -> User:
        return User(**{f: getattr(row, f) for f in _USER_FIELDS})

    def get(self, user_id: uuid.UUID) -> User | None:
        row = self._session.get(UserModel, user_id)
        return self._to_entity(row) if row else None

    def get_by_mobile(self, mobile: str) -> User | None:
        row = self._session.scalar(sa.select(UserModel).where(UserModel.mobile == mobile))
        return self._to_entity(row) if row else None

    def add(self, user: User) -> None:
        row = UserModel()
        _copy(user, row, _USER_FIELDS)
        self._session.add(row)
        self._session.flush()

    def save(self, user: User) -> None:
        _copy(user, self._session.get(UserModel, user.id), _USER_FIELDS)
        self._session.flush()


class SqlAlchemyOtpRepository:
    def __init__(self, session: OrmSession):
        self._session = session

    def latest_for_mobile(self, mobile: str, *, lock: bool = False) -> OtpChallenge | None:
        query = (
            sa.select(OtpCodeModel)
            .where(OtpCodeModel.mobile == mobile)
            .order_by(OtpCodeModel.created_at.desc())
            .limit(1)
        )
        if lock:
            # Re-read the row under the lock, not a copy loaded earlier in this session.
            query = query.with_for_update().execution_options(populate_existing=True)
        row = self._session.scalar(query)
        if row is None:
            return None
        values = {f: getattr(row, f) for f in _OTP_FIELDS}
        values["request_ip"] = _ip(values["request_ip"])
        return OtpChallenge(**values)

    def lock_sending(self, mobile: str, ip: str | None) -> None:
        # Transaction-level advisory locks, released at commit. Always number first, then
        # network, so two requests never wait on each other in opposite order.
        for key in (f"otp:mobile:{mobile}", f"otp:ip:{ip}" if ip else None):
            if key:
                self._session.execute(
                    sa.text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": key}
                )

    def count_for_mobile_since(self, mobile: str, since: datetime) -> int:
        return self._session.scalar(
            sa.select(sa.func.count())
            .select_from(OtpCodeModel)
            .where(OtpCodeModel.mobile == mobile, OtpCodeModel.created_at >= since)
        )

    def count_for_ip_since(self, ip: str, since: datetime) -> int:
        return self._session.scalar(
            sa.select(sa.func.count())
            .select_from(OtpCodeModel)
            .where(OtpCodeModel.request_ip == ip, OtpCodeModel.created_at >= since)
        )

    def add(self, challenge: OtpChallenge) -> None:
        row = OtpCodeModel()
        _copy(challenge, row, _OTP_FIELDS)
        self._session.add(row)
        self._session.flush()

    def save(self, challenge: OtpChallenge) -> None:
        _copy(challenge, self._session.get(OtpCodeModel, challenge.id), _OTP_FIELDS)
        self._session.flush()

    def discard(self, challenge: OtpChallenge) -> None:
        self._session.execute(sa.delete(OtpCodeModel).where(OtpCodeModel.id == challenge.id))


class SqlAlchemySessionRepository:
    def __init__(self, session: OrmSession):
        self._session = session

    def get(self, session_id: uuid.UUID, *, lock: bool = False) -> Session | None:
        return self._one(UserSessionModel.id == session_id, lock)

    def get_by_refresh_token_hash(self, token_hash: str, *, lock: bool = False) -> Session | None:
        return self._one(UserSessionModel.refresh_token_hash == token_hash, lock)

    def _one(self, condition, lock: bool) -> Session | None:
        query = sa.select(UserSessionModel).where(condition)
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        row = self._session.scalar(query)
        if row is None:
            return None
        values = {f: getattr(row, f) for f in _SESSION_FIELDS}
        values["ip_address"] = _ip(values["ip_address"])
        return Session(**values)

    def add(self, session: Session) -> None:
        row = UserSessionModel()
        _copy(session, row, _SESSION_FIELDS)
        self._session.add(row)
        self._session.flush()

    def save(self, session: Session) -> None:
        _copy(session, self._session.get(UserSessionModel, session.id), _SESSION_FIELDS)
        self._session.flush()
