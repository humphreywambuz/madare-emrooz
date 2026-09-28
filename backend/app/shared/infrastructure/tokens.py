"""Signed, expiring access tokens.

The identity module will issue these after OTP verification; the API layer
verifies them on every request.
"""
import uuid
from dataclasses import dataclass

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.shared.domain.errors import AuthenticationError


@dataclass(frozen=True)
class TokenClaims:
    user_id: uuid.UUID
    role: str


class AccessTokenService:
    _SALT = "access-token"

    def __init__(self, secret_key: str, ttl_seconds: int):
        self._serializer = URLSafeTimedSerializer(secret_key, salt=self._SALT)
        self._ttl = ttl_seconds

    def issue(self, user_id: uuid.UUID, role: str) -> str:
        return self._serializer.dumps({"sub": str(user_id), "role": role})

    def verify(self, token: str) -> TokenClaims:
        try:
            payload = self._serializer.loads(token, max_age=self._ttl)
        except SignatureExpired as exc:
            raise AuthenticationError("Access token has expired.") from exc
        except BadSignature as exc:
            raise AuthenticationError("Access token is invalid.") from exc
        return TokenClaims(user_id=uuid.UUID(payload["sub"]), role=payload["role"])
