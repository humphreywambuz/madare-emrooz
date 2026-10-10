"""One-time codes and refresh tokens. Standard library only."""
import base64
import hashlib
import hmac
import secrets
import uuid

OTP_LENGTH = 6


def new_otp_code() -> str:
    return f"{secrets.randbelow(10**OTP_LENGTH):0{OTP_LENGTH}d}"


def hash_otp_code(secret_key: str, mobile: str, code: str) -> str:
    """Keyed hash: a six-digit code has too little entropy for a plain hash,
    so a leaked table cannot be brute-forced without the server secret."""
    message = f"{mobile}:{code}".encode()
    return hmac.new(secret_key.encode(), message, hashlib.sha256).hexdigest()


def otp_code_matches(secret_key: str, mobile: str, code: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_otp_code(secret_key, mobile, code), expected_hash)


def refresh_token_for(secret_key: str, session_id: uuid.UUID, generation: int) -> str:
    """A session's refresh token at one generation: "<session id>.<generation>.<signature>".

    Signed with the server secret rather than random, so a token that has already been
    replaced is still recognised as this session's, and its reuse can end the session.
    """
    message = b"refresh-token:" + session_id.bytes + generation.to_bytes(8, "big")
    digest = hmac.new(secret_key.encode(), message, hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return f"{session_id.hex}.{generation}.{signature}"


def parse_refresh_token(secret_key: str, token: str) -> tuple[uuid.UUID, int] | None:
    """(session id, generation) of a genuine refresh token; None for anything else."""
    parts = (token or "").split(".")
    if len(parts) != 3 or not parts[1].isdigit() or len(parts[1]) > 18:
        return None
    try:
        session_id = uuid.UUID(hex=parts[0])
    except ValueError:
        return None
    generation = int(parts[1])
    if not hmac.compare_digest(refresh_token_for(secret_key, session_id, generation), token):
        return None
    return session_id, generation


def hash_refresh_token(token: str) -> str:
    # The stored lookup key of the current token. The token is a 256-bit HMAC (or, for
    # sessions opened before signed tokens, 256 random bits), so an unkeyed hash is enough.
    return hashlib.sha256(token.encode()).hexdigest()
