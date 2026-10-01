"""Sign-in with a one-time SMS code (spec section 1, proposal section 5-3).

Signing in with a new mobile number creates the account, so there is no
separate sign-up step. Whether the user still needs onboarding is answered by
the profiles module (no profile yet = new user).
"""
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.modules.audit.application.trail import AuditEvent, AuditTrail
from app.modules.audit.domain.enums import AuditEventType
from app.modules.identity.domain.entities import OtpChallenge, Session, User
from app.modules.identity.domain.mobile import normalize_iranian_mobile, to_ascii_digits
from app.modules.identity.domain.secrets import (
    hash_otp_code,
    hash_refresh_token,
    new_otp_code,
    new_refresh_token,
    otp_code_matches,
)
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import (
    AuthenticationError,
    NotFoundError,
    RateLimitedError,
    ServiceUnavailableError,
    ValidationError,
)

from .ports import (
    AccessTokenIssuer,
    OtpRepository,
    SessionRepository,
    SmsDeliveryError,
    SmsSender,
    UserRepository,
)


@dataclass(frozen=True)
class OtpPolicy:
    code_ttl_seconds: int = 120
    resend_cooldown_seconds: int = 60
    max_per_mobile_per_hour: int = 5
    max_per_ip_per_hour: int = 20
    max_attempts: int = 5


@dataclass(frozen=True)
class OtpRequested:
    mobile: str
    expires_in_seconds: int
    resend_after_seconds: int


@dataclass(frozen=True)
class SignedIn:
    access_token: str
    access_token_expires_in: int
    refresh_token: str
    refresh_token_expires_at: datetime
    user_id: uuid.UUID
    role: str
    is_new_user: bool


@dataclass(frozen=True)
class RequestContext:
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass(frozen=True)
class UserView:
    id: uuid.UUID
    mobile: str
    role: str
    mobile_verified_at: datetime | None
    last_login_at: datetime | None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuthService:
    def __init__(
        self,
        *,
        users: UserRepository,
        otps: OtpRepository,
        sessions: SessionRepository,
        sms: SmsSender,
        tokens: AccessTokenIssuer,
        audit: AuditTrail,
        uow: UnitOfWork,
        secret_key: str,
        access_token_ttl_seconds: int,
        refresh_token_ttl: timedelta,
        policy: OtpPolicy = OtpPolicy(),
        now: Callable[[], datetime] = _utcnow,
        generate_code: Callable[[], str] = new_otp_code,
    ):
        self._users = users
        self._otps = otps
        self._sessions = sessions
        self._sms = sms
        self._tokens = tokens
        self._audit = audit
        self._uow = uow
        self._secret_key = secret_key
        self._access_ttl = access_token_ttl_seconds
        self._refresh_ttl = refresh_token_ttl
        self._policy = policy
        self._now = now
        self._generate_code = generate_code

    # --- Step 1: send a code -------------------------------------------------

    def request_otp(self, raw_mobile: str, context: RequestContext) -> OtpRequested:
        """Send a code. The response is the same whether or not the number has an
        account, so the endpoint cannot be used to discover who is registered."""
        mobile = normalize_iranian_mobile(raw_mobile)
        now = self._now()
        self._enforce_send_limits(mobile, context.ip_address, now)

        code = self._generate_code()
        challenge = OtpChallenge(
            mobile=mobile,
            code_hash=hash_otp_code(self._secret_key, mobile, code),
            created_at=now,
            expires_at=now + timedelta(seconds=self._policy.code_ttl_seconds),
            request_ip=context.ip_address,
        )
        self._otps.add(challenge)
        self._uow.commit()
        # Send after committing: a code the user receives must exist in the database.
        try:
            self._sms.send_login_code(mobile, code)
        except SmsDeliveryError:
            # Forget the unsent code so it doesn't count towards the resend limits.
            self._otps.discard(challenge)
            self._uow.commit()
            raise ServiceUnavailableError(
                "We couldn't send the code. Please try again in a moment."
            ) from None
        return OtpRequested(
            mobile=mobile,
            expires_in_seconds=self._policy.code_ttl_seconds,
            resend_after_seconds=self._policy.resend_cooldown_seconds,
        )

    def _enforce_send_limits(self, mobile: str, ip: str | None, now: datetime) -> None:
        latest = self._otps.latest_for_mobile(mobile)
        if latest is not None:
            wait = self._policy.resend_cooldown_seconds - (now - latest.created_at).total_seconds()
            if wait > 0:
                raise RateLimitedError(
                    "Please wait before requesting another code.", retry_after_seconds=int(wait) + 1
                )
        hour_ago = now - timedelta(hours=1)
        if self._otps.count_for_mobile_since(mobile, hour_ago) >= self._policy.max_per_mobile_per_hour:
            raise RateLimitedError(
                "Too many codes requested for this number. Try again later.",
                retry_after_seconds=3600,
            )
        if ip and self._otps.count_for_ip_since(ip, hour_ago) >= self._policy.max_per_ip_per_hour:
            raise RateLimitedError(
                "Too many codes requested from this network. Try again later.",
                retry_after_seconds=3600,
            )

    # --- Step 2: verify the code and sign in ----------------------------------

    def verify_otp(self, raw_mobile: str, raw_code: str, context: RequestContext) -> SignedIn:
        mobile = normalize_iranian_mobile(raw_mobile)
        code = to_ascii_digits(raw_code or "").strip()
        now = self._now()

        challenge = self._otps.latest_for_mobile(mobile)
        if challenge is None or challenge.consumed_at is not None or challenge.is_expired(now):
            raise ValidationError(
                "This code has expired. Request a new one.", details={"reason": "expired"}
            )
        if challenge.attempts_left(self._policy.max_attempts) == 0:
            raise ValidationError(
                "Too many wrong codes. Request a new one.", details={"reason": "too_many_attempts"}
            )
        if not otp_code_matches(self._secret_key, mobile, code, challenge.code_hash):
            challenge.register_failed_attempt()
            self._otps.save(challenge)
            user = self._users.get_by_mobile(mobile)
            self._audit.record(
                AuditEvent(
                    AuditEventType.LOGIN_FAILED,
                    actor_id=user.id if user else None,
                    ip_address=context.ip_address,
                    user_agent=context.user_agent,
                    details={"reason": "wrong_code", "attempts": challenge.attempts},
                )
            )
            # Commit before raising: the failed attempt must count even though
            # the request ends in an error.
            self._uow.commit()
            raise ValidationError(
                "The code is incorrect.",
                details={
                    "reason": "wrong_code",
                    "attempts_left": challenge.attempts_left(self._policy.max_attempts),
                },
            )

        challenge.consume(now)
        self._otps.save(challenge)

        user = self._users.get_by_mobile(mobile)
        is_new_user = user is None
        if user is None:
            user = User(mobile=mobile)
            self._users.add(user)
        elif not user.is_active:
            self._uow.commit()  # keep the code consumed
            raise AuthenticationError("This account is no longer active.")
        user.record_login(now)
        self._users.save(user)

        signed_in = self._open_session(user, context, now, is_new_user)
        self._audit.record(
            AuditEvent(
                AuditEventType.LOGIN_SUCCEEDED,
                actor_id=user.id,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                details={"new_user": is_new_user},
            )
        )
        self._uow.commit()
        return signed_in

    # --- Keeping the session alive ---------------------------------------------

    def refresh(self, refresh_token: str, context: RequestContext) -> SignedIn:
        now = self._now()
        session = self._sessions.get_by_refresh_token_hash(hash_refresh_token(refresh_token or ""))
        if session is None or not session.is_active(now):
            raise AuthenticationError("Your session has ended. Sign in again.")
        user = self._users.get(session.user_id)
        if user is None or not user.is_active:
            session.revoke(now)
            self._sessions.save(session)
            self._uow.commit()
            raise AuthenticationError("This account is no longer active.")

        new_token = new_refresh_token()
        session.rotate(hash_refresh_token(new_token), now)
        if context.ip_address:
            session.ip_address = context.ip_address
        self._sessions.save(session)
        self._uow.commit()
        return self._signed_in(user, new_token, session, is_new_user=False)

    def logout(self, refresh_token: str) -> None:
        """Always succeeds, so a client can't probe whether a token was valid."""
        session = self._sessions.get_by_refresh_token_hash(hash_refresh_token(refresh_token or ""))
        if session is not None:
            session.revoke(self._now())
            self._sessions.save(session)
            self._uow.commit()

    def get_user(self, user_id: uuid.UUID) -> UserView:
        user = self._users.get(user_id)
        if user is None:
            raise NotFoundError("Account not found.")
        return UserView(
            id=user.id,
            mobile=user.mobile,
            role=user.role.value,
            mobile_verified_at=user.mobile_verified_at,
            last_login_at=user.last_login_at,
        )

    # --- helpers ---------------------------------------------------------------

    def _open_session(
        self, user: User, context: RequestContext, now: datetime, is_new_user: bool
    ) -> SignedIn:
        token = new_refresh_token()
        session = Session(
            user_id=user.id,
            refresh_token_hash=hash_refresh_token(token),
            created_at=now,
            expires_at=now + self._refresh_ttl,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            last_seen_at=now,
        )
        self._sessions.add(session)
        return self._signed_in(user, token, session, is_new_user)

    def _signed_in(self, user: User, refresh_token: str, session: Session, is_new_user: bool) -> SignedIn:
        return SignedIn(
            access_token=self._tokens.issue(user.id, user.role.value),
            access_token_expires_in=self._access_ttl,
            refresh_token=refresh_token,
            refresh_token_expires_at=session.expires_at,
            user_id=user.id,
            role=user.role.value,
            is_new_user=is_new_user,
        )
