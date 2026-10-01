"""Partner Mode, Phase 1: a QR code that lets her spouse see the pregnancy week and due date.

The code holds a link token made of the link id and an HMAC of it keyed with SECRET_KEY,
so the database never stores anything that could be used as a link. The spouse doesn't
sign in; the mother can turn the link off at any time.
"""
import base64
import hashlib
import hmac
import uuid
from dataclasses import dataclass, field
from datetime import datetime

_SIGNATURE_CHARS = 22  # 128 bits, base64url


@dataclass
class PartnerLink:
    user_id: uuid.UUID
    created_at: datetime
    revoked_at: datetime | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None

    def revoke(self, now: datetime) -> None:
        if self.revoked_at is None:
            self.revoked_at = now


def _signature(secret_key: str, link_id: uuid.UUID) -> str:
    digest = hmac.new(secret_key.encode(), b"partner-link:" + link_id.bytes, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode()[:_SIGNATURE_CHARS]


def partner_token(secret_key: str, link_id: uuid.UUID) -> str:
    return link_id.hex + _signature(secret_key, link_id)


def parse_partner_token(secret_key: str, token: str) -> uuid.UUID | None:
    """The link id, or None if the token was not issued by this server."""
    if len(token) != 32 + _SIGNATURE_CHARS:
        return None
    try:
        link_id = uuid.UUID(hex=token[:32])
    except ValueError:
        return None
    if not hmac.compare_digest(token[32:], _signature(secret_key, link_id)):
        return None
    return link_id
