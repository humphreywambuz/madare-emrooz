"""Sign-in use cases with in-memory fakes and a controllable clock."""
from datetime import datetime, timedelta, timezone

import pytest

from app.modules.audit.domain.enums import AuditEventType
from app.modules.identity.application.ports import SmsDeliveryError
from app.modules.identity.application.services import AuthService, OtpPolicy, RequestContext
from app.shared.domain.errors import (
    AuthenticationError,
    RateLimitedError,
    ServiceUnavailableError,
    ValidationError,
)

MOBILE = "09121234567"
E164 = "+989121234567"
CTX = RequestContext(ip_address="192.0.2.1", user_agent="tests")


class Clock:
    def __init__(self):
        self.now = datetime(2026, 9, 30, 8, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.now

    def advance(self, **kwargs):
        self.now += timedelta(**kwargs)


class Repo:
    """Generic in-memory repository keyed by entity id."""

    def __init__(self):
        self.items = {}

    def add(self, item):
        self.items[item.id] = item

    save = add


class Users(Repo):
    def get(self, user_id):
        return self.items.get(user_id)

    def get_by_mobile(self, mobile):
        return next((u for u in self.items.values() if u.mobile == mobile), None)


class Otps(Repo):
    def discard(self, challenge):
        del self.items[challenge.id]

    def latest_for_mobile(self, mobile):
        mine = [c for c in self.items.values() if c.mobile == mobile]
        return max(mine, key=lambda c: c.created_at, default=None)

    def count_for_mobile_since(self, mobile, since):
        return sum(1 for c in self.items.values() if c.mobile == mobile and c.created_at >= since)

    def count_for_ip_since(self, ip, since):
        return sum(1 for c in self.items.values() if c.request_ip == ip and c.created_at >= since)


class Sessions(Repo):
    def get_by_refresh_token_hash(self, token_hash):
        return next((s for s in self.items.values() if s.refresh_token_hash == token_hash), None)


class Sms:
    def __init__(self):
        self.sent = []
        self.failing = False

    def send_login_code(self, mobile, code):
        if self.failing:
            raise SmsDeliveryError("gateway down")
        self.sent.append((mobile, code))

    @property
    def last_code(self):
        return self.sent[-1][1]


class Tokens:
    def issue(self, user_id, role):
        return f"access:{user_id}:{role}"


class Audit:
    def __init__(self):
        self.events = []

    def record(self, event):
        self.events.append(event)


class Uow:
    commits = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass


@pytest.fixture()
def env():
    clock, sms, audit, uow = Clock(), Sms(), Audit(), Uow()
    users, otps, sessions = Users(), Otps(), Sessions()
    service = AuthService(
        users=users, otps=otps, sessions=sessions, sms=sms, tokens=Tokens(), audit=audit, uow=uow,
        secret_key="test-secret", access_token_ttl_seconds=900, refresh_token_ttl=timedelta(days=30),
        policy=OtpPolicy(max_per_ip_per_hour=3), now=clock,
        generate_code=lambda codes=iter(range(100001, 999999)): str(next(codes)),
    )

    class Env:
        pass

    e = Env()
    e.__dict__.update(service=service, clock=clock, sms=sms, audit=audit, uow=uow, users=users, otps=otps, sessions=sessions)
    return e


def sign_in(env, mobile=MOBILE):
    env.service.request_otp(mobile, CTX)
    return env.service.verify_otp(mobile, env.sms.last_code, CTX)


def test_request_sends_a_six_digit_code_and_stores_only_its_hash(env):
    sent = env.service.request_otp(MOBILE, CTX)
    assert sent.mobile == E164
    (mobile, code), = env.sms.sent
    assert mobile == E164 and len(code) == 6 and code.isdigit()
    (challenge,) = env.otps.items.values()
    assert code not in challenge.code_hash
    assert challenge.request_ip == "192.0.2.1"


def test_first_sign_in_creates_the_account(env):
    result = sign_in(env)
    assert result.is_new_user is True
    user = env.users.get(result.user_id)
    assert user.mobile == E164 and user.mobile_verified_at == env.clock.now
    assert result.access_token.startswith(f"access:{user.id}:user")
    assert [e.event_type for e in env.audit.events] == [AuditEventType.LOGIN_SUCCEEDED]


def test_second_sign_in_finds_the_same_account(env):
    first = sign_in(env)
    env.clock.advance(minutes=5)
    second = sign_in(env, "+98 912 123 4567")
    assert second.is_new_user is False
    assert second.user_id == first.user_id
    assert len(env.users.items) == 1


def test_resend_cooldown(env):
    env.service.request_otp(MOBILE, CTX)
    env.clock.advance(seconds=20)
    with pytest.raises(RateLimitedError) as exc:
        env.service.request_otp(MOBILE, CTX)
    assert exc.value.retry_after_seconds == 41
    env.clock.advance(seconds=41)
    env.service.request_otp(MOBILE, CTX)


def test_hourly_limit_per_mobile(env):
    ctx = RequestContext()  # no IP, so only the per-mobile limit applies
    for _ in range(5):
        env.service.request_otp(MOBILE, ctx)
        env.clock.advance(seconds=61)
    with pytest.raises(RateLimitedError):
        env.service.request_otp(MOBILE, ctx)
    env.clock.advance(hours=1)
    env.service.request_otp(MOBILE, ctx)


def test_hourly_limit_per_network(env):
    for n in range(3):
        env.service.request_otp(f"0912000000{n}", CTX)
    with pytest.raises(RateLimitedError):
        env.service.request_otp("09120000009", CTX)


def test_wrong_code_counts_attempts_and_is_committed(env):
    env.service.request_otp(MOBILE, CTX)
    commits_before = env.uow.commits
    with pytest.raises(ValidationError) as exc:
        env.service.verify_otp(MOBILE, "000000", CTX)
    assert exc.value.details == {"reason": "wrong_code", "attempts_left": 4}
    assert env.uow.commits == commits_before + 1
    assert env.audit.events[-1].event_type is AuditEventType.LOGIN_FAILED


def test_code_locks_after_max_attempts(env):
    env.service.request_otp(MOBILE, CTX)
    right = env.sms.last_code
    for _ in range(5):
        with pytest.raises(ValidationError):
            env.service.verify_otp(MOBILE, "000000", CTX)
    with pytest.raises(ValidationError) as exc:
        env.service.verify_otp(MOBILE, right, CTX)
    assert exc.value.details["reason"] == "too_many_attempts"


def test_expired_code_is_rejected(env):
    env.service.request_otp(MOBILE, CTX)
    env.clock.advance(seconds=121)
    with pytest.raises(ValidationError) as exc:
        env.service.verify_otp(MOBILE, env.sms.last_code, CTX)
    assert exc.value.details["reason"] == "expired"


def test_code_works_only_once(env):
    env.service.request_otp(MOBILE, CTX)
    code = env.sms.last_code
    env.service.verify_otp(MOBILE, code, CTX)
    with pytest.raises(ValidationError):
        env.service.verify_otp(MOBILE, code, CTX)


def test_new_code_replaces_the_old_one(env):
    env.service.request_otp(MOBILE, CTX)
    old = env.sms.last_code
    env.clock.advance(seconds=61)
    env.service.request_otp(MOBILE, CTX)
    assert env.sms.last_code != old
    with pytest.raises(ValidationError):
        env.service.verify_otp(MOBILE, old, CTX)
    env.service.verify_otp(MOBILE, env.sms.last_code, CTX)


def test_persian_digits_in_code(env):
    env.service.request_otp(MOBILE, CTX)
    persian = env.sms.last_code.translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
    assert env.service.verify_otp(MOBILE, persian, CTX).is_new_user


def test_deactivated_account_cannot_sign_in(env):
    user_id = sign_in(env).user_id
    env.users.get(user_id).is_active = False
    env.clock.advance(minutes=2)
    env.service.request_otp(MOBILE, CTX)
    with pytest.raises(AuthenticationError):
        env.service.verify_otp(MOBILE, env.sms.last_code, CTX)


def test_refresh_rotates_the_token(env):
    first = sign_in(env)
    env.clock.advance(minutes=20)
    second = env.service.refresh(first.refresh_token, CTX)
    assert second.refresh_token != first.refresh_token
    assert second.user_id == first.user_id
    with pytest.raises(AuthenticationError):
        env.service.refresh(first.refresh_token, CTX)  # already used


def test_refresh_token_expires(env):
    result = sign_in(env)
    env.clock.advance(days=31)
    with pytest.raises(AuthenticationError):
        env.service.refresh(result.refresh_token, CTX)


def test_refresh_rejected_for_deactivated_account(env):
    result = sign_in(env)
    env.users.get(result.user_id).is_active = False
    with pytest.raises(AuthenticationError):
        env.service.refresh(result.refresh_token, CTX)
    (session,) = env.sessions.items.values()
    assert session.revoked_at is not None


def test_logout_ends_the_session(env):
    result = sign_in(env)
    env.service.logout(result.refresh_token)
    with pytest.raises(AuthenticationError):
        env.service.refresh(result.refresh_token, CTX)
    env.service.logout("unknown-token")  # no error either way


def test_a_code_that_could_not_be_sent_is_forgotten(env):
    env.sms.failing = True
    with pytest.raises(ServiceUnavailableError):
        env.service.request_otp(MOBILE, CTX)
    assert env.otps.items == {}

    # The failed attempt doesn't trigger the resend cooldown.
    env.sms.failing = False
    env.service.request_otp(MOBILE, CTX)
    assert len(env.sms.sent) == 1
