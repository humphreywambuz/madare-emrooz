"""One-time codes and refresh tokens. Standard library only."""
import hashlib
import hmac
import secrets

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


def new_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    # Refresh tokens carry 256 bits of randomness, so an unkeyed hash is enough.
    return hashlib.sha256(token.encode()).hexdigest()
