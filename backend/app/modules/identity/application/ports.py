import uuid
from datetime import datetime
from typing import Protocol

from app.modules.identity.domain.entities import OtpChallenge, Session, User


class UserRepository(Protocol):
    def get(self, user_id: uuid.UUID) -> User | None: ...

    def get_by_mobile(self, mobile: str) -> User | None: ...

    def add(self, user: User) -> None: ...

    def save(self, user: User) -> None: ...


class OtpRepository(Protocol):
    def latest_for_mobile(self, mobile: str) -> OtpChallenge | None: ...

    def count_for_mobile_since(self, mobile: str, since: datetime) -> int: ...

    def count_for_ip_since(self, ip: str, since: datetime) -> int: ...

    def add(self, challenge: OtpChallenge) -> None: ...

    def discard(self, challenge: OtpChallenge) -> None: ...

    def save(self, challenge: OtpChallenge) -> None: ...


class SessionRepository(Protocol):
    def get_by_refresh_token_hash(self, token_hash: str) -> Session | None: ...

    def add(self, session: Session) -> None: ...

    def save(self, session: Session) -> None: ...


class SmsDeliveryError(Exception):
    """Raised by an SmsSender when the provider did not accept the message."""


class SmsSender(Protocol):
    def send_login_code(self, mobile: str, code: str) -> None:
        """Send a sign-in code to ``mobile`` (+989…). Raises SmsDeliveryError on failure."""


class AccessTokenIssuer(Protocol):
    def issue(self, user_id: uuid.UUID, role: str) -> str: ...
