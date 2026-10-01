import os


# Placeholder keys from this repository; the app refuses them when it sends real SMS.
DEVELOPMENT_SECRET_KEYS = frozenset({"dev-secret-key", "change-me"})


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    # Number of reverse proxies in front of the app (e.g. 1 for nginx). Their
    # X-Forwarded-For/-Proto/-Host headers are then trusted, so per-network OTP limits and
    # the audit log see each client's own address. Leave 0 when nothing is in front.
    TRUSTED_PROXY_COUNT = int(os.environ.get("TRUSTED_PROXY_COUNT", 0))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/madare_emrooz",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    # Short-lived access tokens; clients renew them with the refresh token.
    ACCESS_TOKEN_TTL_SECONDS = int(os.environ.get("ACCESS_TOKEN_TTL_SECONDS", 15 * 60))
    REFRESH_TOKEN_TTL_DAYS = int(os.environ.get("REFRESH_TOKEN_TTL_DAYS", 30))

    # "kavenegar" sends real SMS. "console" logs codes instead (development only).
    SMS_BACKEND = os.environ.get("SMS_BACKEND", "console")
    KAVENEGAR_API_KEY = os.environ.get("KAVENEGAR_API_KEY", "")
    # Verify template defined in the Kavenegar panel; its text contains %token.
    KAVENEGAR_OTP_TEMPLATE = os.environ.get("KAVENEGAR_OTP_TEMPLATE", "madareemrooz-otp")
    OTP_CODE_TTL_SECONDS = int(os.environ.get("OTP_CODE_TTL_SECONDS", 120))
    OTP_RESEND_COOLDOWN_SECONDS = int(os.environ.get("OTP_RESEND_COOLDOWN_SECONDS", 60))
    OTP_MAX_PER_MOBILE_PER_HOUR = int(os.environ.get("OTP_MAX_PER_MOBILE_PER_HOUR", 5))
    OTP_MAX_PER_IP_PER_HOUR = int(os.environ.get("OTP_MAX_PER_IP_PER_HOUR", 20))
    # Base of the partner QR link, e.g. https://madaremrooz.ir (defaults to the request's host).
    PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "")
    # Medical documents (JPEG, PNG or PDF) are stored in PostgreSQL.
    DOCUMENT_MAX_BYTES = int(os.environ.get("DOCUMENT_MAX_BYTES", 10 * 1024 * 1024))
    # Requests larger than this are refused before they are read (413).
    MAX_CONTENT_LENGTH = DOCUMENT_MAX_BYTES + 1024 * 1024
    # "all" in Phase 1: doctors see every mother. "assigned" in Phase 2, once mothers
    # choose their gynecologist / referring doctor.
    DOCTOR_PATIENT_SCOPE = os.environ.get("DOCTOR_PATIENT_SCOPE", "all")
    OTP_MAX_ATTEMPTS = int(os.environ.get("OTP_MAX_ATTEMPTS", 5))
    # Message text for the console and memory backends; Kavenegar uses its own template.
    OTP_SMS_TEMPLATE = os.environ.get("OTP_SMS_TEMPLATE", "کد ورود شما: {code}")


class TestConfig(Config):
    TESTING = True
    SMS_BACKEND = "memory"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/madare_emrooz_test",
    )
