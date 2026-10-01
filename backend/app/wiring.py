"""Composition root for use cases.

Builds each use case with its concrete adapters for the current request. This
is the only place (with create_app) allowed to combine infrastructure from
several modules; module api layers import their service factories from here.
"""
from datetime import timedelta

from flask import current_app

from app.extensions import db
from app.modules.audit.infrastructure.trail import SqlAlchemyAuditTrail
from app.modules.care_team.application.services import CareTeamService, StaffService
from app.modules.care_team.domain.enums import AlertKind, ApprovalScope, DoctorPatientScope
from app.modules.care_team.infrastructure.repositories import (
    SqlAlchemyAlertRepository,
    SqlAlchemyApprovalRepository,
    SqlAlchemyCareAssignmentRepository,
    SqlAlchemyPatientDirectory,
    SqlAlchemyStaffDirectory,
    SqlAlchemyStaffProfileRepository,
)
from app.modules.documents.application.services import DocumentService
from app.modules.documents.infrastructure.repositories import SqlAlchemyDocumentRepository
from app.modules.fitness.application.services import FitnessService
from app.modules.fitness.infrastructure.repositories import SqlAlchemyFitnessProfileRepository
from app.modules.identity.application.services import AuthService, OtpPolicy, UserAccounts
from app.modules.identity.infrastructure.repositories import (
    SqlAlchemyOtpRepository,
    SqlAlchemySessionRepository,
    SqlAlchemyUserRepository,
)
from app.modules.identity.infrastructure.sms import (
    ConsoleSmsSender,
    InMemorySmsSender,
    KavenegarSmsSender,
)
from app.modules.monitoring.application.services import MonitoringService
from app.modules.monitoring.infrastructure.repositories import SqlAlchemyDailyLogRepository
from app.modules.pregnancy.application.partner import PartnerService
from app.modules.pregnancy.application.services import PregnancyService
from app.modules.profiles.application.services import ProfileService
from app.modules.profiles.infrastructure.repositories import (
    SqlAlchemyMedicalHistoryRepository,
    SqlAlchemyProfileRepository,
)
from app.modules.pregnancy.infrastructure.repository import (
    SqlAlchemyPartnerLinkRepository,
    SqlAlchemyPregnancyRepository,
)
from app.modules.rehabilitation.application.services import RehabService
from app.modules.rehabilitation.infrastructure.repositories import SqlAlchemyRehabProfileRepository
from app.shared.api.auth import token_service
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


def sms_sender():
    c = current_app.config
    backend = c["SMS_BACKEND"]
    if backend == "kavenegar":
        return KavenegarSmsSender(c["KAVENEGAR_API_KEY"], c["KAVENEGAR_OTP_TEMPLATE"])
    if backend == "console":
        return ConsoleSmsSender(c["OTP_SMS_TEMPLATE"])
    if backend == "memory":
        outbox = current_app.extensions.setdefault("sms_outbox", [])
        return InMemorySmsSender(outbox, c["OTP_SMS_TEMPLATE"])
    raise RuntimeError(f"Unknown SMS_BACKEND {backend!r}")


def otp_policy() -> OtpPolicy:
    c = current_app.config
    return OtpPolicy(
        code_ttl_seconds=c["OTP_CODE_TTL_SECONDS"],
        resend_cooldown_seconds=c["OTP_RESEND_COOLDOWN_SECONDS"],
        max_per_mobile_per_hour=c["OTP_MAX_PER_MOBILE_PER_HOUR"],
        max_per_ip_per_hour=c["OTP_MAX_PER_IP_PER_HOUR"],
        max_attempts=c["OTP_MAX_ATTEMPTS"],
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


def profile_service() -> ProfileService:
    session = db.session
    return ProfileService(
        SqlAlchemyProfileRepository(session),
        SqlAlchemyMedicalHistoryRepository(session),
        SqlAlchemyAuditTrail(session),
        SqlAlchemyUnitOfWork(session),
    )


def pregnancy_service() -> PregnancyService:
    return PregnancyService(
        SqlAlchemyPregnancyRepository(db.session),
        SqlAlchemyUnitOfWork(db.session),
        # A birth switches her home to the postpartum paths (fitness and rehabilitation).
        on_delivered=profile_service().record_delivery,
    )


def staff_service() -> StaffService:
    session = db.session
    return StaffService(
        accounts=UserAccounts(SqlAlchemyUserRepository(session)),
        profiles=SqlAlchemyStaffProfileRepository(session),
        directory=SqlAlchemyStaffDirectory(session),
        assignments=SqlAlchemyCareAssignmentRepository(session),
        audit=SqlAlchemyAuditTrail(session),
        uow=SqlAlchemyUnitOfWork(session),
    )


def care_team_service() -> CareTeamService:
    session = db.session
    return CareTeamService(
        assignments=SqlAlchemyCareAssignmentRepository(session),
        alerts=SqlAlchemyAlertRepository(session),
        patients=SqlAlchemyPatientDirectory(session),
        audit=SqlAlchemyAuditTrail(session),
        uow=SqlAlchemyUnitOfWork(session),
        doctor_scope=DoctorPatientScope(current_app.config["DOCTOR_PATIENT_SCOPE"]),
    )


def monitoring_service() -> MonitoringService:
    session = db.session
    care_team = care_team_service()
    return MonitoringService(
        logs=SqlAlchemyDailyLogRepository(session),
        active_pregnancy_id=pregnancy_service().active_pregnancy_id,
        on_bleeding=lambda patient_id, log_id: care_team.raise_alert(
            patient_id, AlertKind.BLEEDING, log_id
        ),
        access=care_team,
        audit=SqlAlchemyAuditTrail(session),
        uow=SqlAlchemyUnitOfWork(session),
    )


def document_service() -> DocumentService:
    session = db.session
    return DocumentService(
        documents=SqlAlchemyDocumentRepository(session),
        active_pregnancy_id=pregnancy_service().active_pregnancy_id,
        access=care_team_service(),
        audit=SqlAlchemyAuditTrail(session),
        uow=SqlAlchemyUnitOfWork(session),
        max_file_bytes=current_app.config["DOCUMENT_MAX_BYTES"],
    )


def fitness_service() -> FitnessService:
    session = db.session
    return FitnessService(
        profiles=SqlAlchemyFitnessProfileRepository(session),
        access=care_team_service(),
        audit=SqlAlchemyAuditTrail(session),
        uow=SqlAlchemyUnitOfWork(session),
    )


def rehab_service() -> RehabService:
    session = db.session
    approvals = SqlAlchemyApprovalRepository(session)
    return RehabService(
        profiles=SqlAlchemyRehabProfileRepository(session),
        has_plan_approval=lambda patient_id: approvals.active(
            patient_id, ApprovalScope.REHABILITATION_PLAN
        ) is not None,
        require_document_of=document_service().require_document_of,
        access=care_team_service(),
        audit=SqlAlchemyAuditTrail(session),
        uow=SqlAlchemyUnitOfWork(session),
    )


def partner_service() -> PartnerService:
    session = db.session
    return PartnerService(
        links=SqlAlchemyPartnerLinkRepository(session),
        pregnancies=SqlAlchemyPregnancyRepository(session),
        audit=SqlAlchemyAuditTrail(session),
        uow=SqlAlchemyUnitOfWork(session),
        secret_key=current_app.config["SECRET_KEY"],
    )
