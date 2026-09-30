"""Composition root for use cases.

Builds each use case with its concrete adapters for the current request. This
is the only place (with create_app) allowed to combine infrastructure from
several modules; module api layers import their service factories from here.
"""
from datetime import timedelta

from flask import current_app

from app.extensions import db
from app.modules.audit.infrastructure.trail import SqlAlchemyAuditTrail
from app.modules.identity.application.services import AuthService, OtpPolicy
from app.modules.identity.infrastructure.repositories import (
    SqlAlchemyOtpRepository,
    SqlAlchemySessionRepository,
    SqlAlchemyUserRepository,
)
from app.modules.identity.infrastructure.sms import ConsoleSmsSender, InMemorySmsSender
from app.modules.pregnancy.application.services import PregnancyService
from app.modules.pregnancy.infrastructure.repository import SqlAlchemyPregnancyRepository
from app.shared.api.auth import token_service
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


def sms_sender():
    backend = current_app.config["SMS_BACKEND"]
    if backend == "console":
        return ConsoleSmsSender()
    if backend == "memory":
        return InMemorySmsSender(current_app.extensions.setdefault("sms_outbox", []))
    raise RuntimeError(f"Unknown SMS_BACKEND {backend!r}")


def otp_policy() -> OtpPolicy:
    c = current_app.config
    return OtpPolicy(
        code_ttl_seconds=c["OTP_CODE_TTL_SECONDS"],
        resend_cooldown_seconds=c["OTP_RESEND_COOLDOWN_SECONDS"],
        max_per_mobile_per_hour=c["OTP_MAX_PER_MOBILE_PER_HOUR"],
        max_per_ip_per_hour=c["OTP_MAX_PER_IP_PER_HOUR"],
        max_attempts=c["OTP_MAX_ATTEMPTS"],
        sms_template=c["OTP_SMS_TEMPLATE"],
    )


def auth_service() -> AuthService:
    session = db.session
    return AuthService(
        users=SqlAlchemyUserRepository(session),
        otps=SqlAlchemyOtpRepository(session),
        sessions=SqlAlchemySessionRepository(session),
        sms=sms_sender(),
        tokens=token_service(),
        audit=SqlAlchemyAuditTrail(session),
        uow=SqlAlchemyUnitOfWork(session),
        secret_key=current_app.config["SECRET_KEY"],
        access_token_ttl_seconds=current_app.config["ACCESS_TOKEN_TTL_SECONDS"],
        refresh_token_ttl=timedelta(days=current_app.config["REFRESH_TOKEN_TTL_DAYS"]),
        policy=otp_policy(),
    )


def pregnancy_service() -> PregnancyService:
    return PregnancyService(
        SqlAlchemyPregnancyRepository(db.session), SqlAlchemyUnitOfWork(db.session)
    )
