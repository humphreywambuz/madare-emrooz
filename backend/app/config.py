import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/madare_emrooz",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    # Short-lived access tokens; clients renew them with the refresh token.
    ACCESS_TOKEN_TTL_SECONDS = int(os.environ.get("ACCESS_TOKEN_TTL_SECONDS", 15 * 60))
    REFRESH_TOKEN_TTL_DAYS = int(os.environ.get("REFRESH_TOKEN_TTL_DAYS", 30))

    # "console" logs codes instead of sending them (development only).
    SMS_BACKEND = os.environ.get("SMS_BACKEND", "console")
    OTP_CODE_TTL_SECONDS = int(os.environ.get("OTP_CODE_TTL_SECONDS", 120))
    OTP_RESEND_COOLDOWN_SECONDS = int(os.environ.get("OTP_RESEND_COOLDOWN_SECONDS", 60))
    OTP_MAX_PER_MOBILE_PER_HOUR = int(os.environ.get("OTP_MAX_PER_MOBILE_PER_HOUR", 5))
    OTP_MAX_PER_IP_PER_HOUR = int(os.environ.get("OTP_MAX_PER_IP_PER_HOUR", 20))
    OTP_MAX_ATTEMPTS = int(os.environ.get("OTP_MAX_ATTEMPTS", 5))
    OTP_SMS_TEMPLATE = os.environ.get("OTP_SMS_TEMPLATE", "کد ورود شما: {code}")


class TestConfig(Config):
    TESTING = True
    SMS_BACKEND = "memory"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/madare_emrooz_test",
    )
