"""Rules from the Phase 1 data dictionary (section 7: data rules and delete behaviour).

These run against PostgreSQL because the database itself must enforce them.
"""
from datetime import date

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from app.modules.audit.domain.enums import AuditEventType
from app.modules.audit.infrastructure.models import AuditLogModel
from app.modules.care_team.domain.enums import ApprovalScope, RiskTag
from app.modules.care_team.infrastructure.models import (
    CareApprovalModel,
    RiskTagAssignmentModel,
    StaffNoteModel,
)
from app.modules.documents.domain.enums import DocumentType
from app.modules.documents.infrastructure.models import MedicalDocumentModel
from app.modules.fitness.domain.enums import FitnessGoal
from app.modules.fitness.infrastructure.models import FitnessProfileModel
from app.modules.identity.domain.enums import UserRole
from app.modules.identity.infrastructure.models import OtpCodeModel, UserModel, UserSessionModel
from app.modules.monitoring.infrastructure.models import DailyLogModel
from app.modules.pregnancy.domain.enums import ConceptionType
from app.modules.pregnancy.infrastructure.models import PregnancyModel
from app.modules.profiles.domain.enums import JoinGoal
from app.modules.profiles.infrastructure.models import MedicalHistoryModel, ProfileModel
from app.modules.rehabilitation.domain.enums import RehabSubcategory
from app.modules.rehabilitation.infrastructure.models import RehabProfileModel


def count(session, model) -> int:
    return session.scalar(sa.select(sa.func.count()).select_from(model))


def document(patient, uploader, **extra):
    return MedicalDocumentModel(
        patient_id=patient.id,
        uploaded_by_id=uploader.id,
        document_type=DocumentType.IMAGING,
        storage_key=f"docs/{patient.id}/{extra.pop('name', 'scan')}.pdf",
        original_filename="scan.pdf",
        content_type="application/pdf",
        file_size_bytes=100,
        **extra,
    )


@pytest.fixture()
def mother_with_everything(session, make_user):
    """A mother with a row in every table that belongs to her. She recorded one
    daily log herself (a bleeding report); the database also allows her as a document's
    uploader, although the app lets only her midwife upload."""
    mother = make_user()
    doctor = make_user(UserRole.DOCTOR)
    midwife = make_user(UserRole.MIDWIFE)
    pregnancy = PregnancyModel(
        user_id=mother.id, lmp_date=date(2026, 6, 1), conception_type=ConceptionType.NATURAL,
        estimated_due_date=date(2027, 3, 8),
    )
    session.add(pregnancy)
    session.flush()
    scan = document(mother, mother, pregnancy_id=pregnancy.id)
    session.add_all([
        ProfileModel(user_id=mother.id, first_name="Sara", last_name="A", join_goal=JoinGoal.PREGNANCY),
        MedicalHistoryModel(user_id=mother.id),
        FitnessProfileModel(user_id=mother.id, goal=FitnessGoal.GENERAL_FITNESS),
        DailyLogModel(patient_id=mother.id, recorded_by_id=mother.id, pregnancy_id=pregnancy.id,
                      has_spotting_or_bleeding=True),
        DailyLogModel(patient_id=mother.id, recorded_by_id=midwife.id, systolic_bp=110),
        scan,
        document(mother, midwife, name="lab"),
        RiskTagAssignmentModel(patient_id=mother.id, tag=RiskTag.THYROID, added_by_id=doctor.id),
        StaffNoteModel(patient_id=mother.id, author_id=midwife.id, body="ok"),
        CareApprovalModel(patient_id=mother.id, approved_by_id=doctor.id,
                          scope=ApprovalScope.REHABILITATION_PLAN),
        UserSessionModel(user_id=mother.id, refresh_token_hash="h" * 64,
                         expires_at=sa.func.now() + sa.text("interval '1 day'")),
        AuditLogModel(actor_id=mother.id, patient_id=mother.id,
                      event_type=AuditEventType.LOGIN_SUCCEEDED),
    ])
    session.flush()
    session.add(RehabProfileModel(
        user_id=mother.id, subcategory=RehabSubcategory.ORTHOPEDIC_REFERRAL, pain_level=3,
        had_related_surgery=False, uses_pain_medication=False, imaging_document_id=scan.id,
    ))
    session.flush()
    return {"mother": mother, "doctor": doctor, "midwife": midwife, "pregnancy": pregnancy, "scan": scan}


# --- Delete behaviour (table on the last page) -------------------------------

def test_deleting_a_mother_deletes_all_her_data_but_keeps_the_audit_log(session, mother_with_everything):
    session.delete(mother_with_everything["mother"])
    session.flush()
    for model in (
        ProfileModel, MedicalHistoryModel, FitnessProfileModel, RehabProfileModel, PregnancyModel,
        DailyLogModel, MedicalDocumentModel, RiskTagAssignmentModel, StaffNoteModel,
        CareApprovalModel, UserSessionModel,
    ):
        assert count(session, model) == 0, model.__tablename__
    assert count(session, AuditLogModel) == 1
    assert count(session, UserModel) == 2  # doctor and midwife remain


@pytest.mark.parametrize("staff", ["doctor", "midwife"])
def test_staff_with_records_cannot_be_deleted(session, mother_with_everything, staff):
    session.delete(mother_with_everything[staff])
    with pytest.raises(IntegrityError):
        session.flush()


def test_deleting_a_pregnancy_keeps_logs_and_documents_and_clears_their_link(session, mother_with_everything):
    session.delete(mother_with_everything["pregnancy"])
    session.flush()
    assert count(session, DailyLogModel) == 2
    assert count(session, MedicalDocumentModel) == 2
    assert session.scalar(sa.select(sa.func.count()).where(DailyLogModel.pregnancy_id.is_not(None))) == 0
    assert session.scalar(sa.select(sa.func.count()).where(MedicalDocumentModel.pregnancy_id.is_not(None))) == 0


def test_deleting_a_document_keeps_the_rehab_profile_and_clears_the_imaging_link(session, mother_with_everything):
    session.delete(mother_with_everything["scan"])
    session.flush()
    rehab = session.scalar(sa.select(RehabProfileModel))
    session.refresh(rehab)
    assert rehab.imaging_document_id is None


# --- Data rules (bullet list in section 7) -----------------------------------

@pytest.mark.parametrize("model", [UserModel, OtpCodeModel])
@pytest.mark.parametrize(
    "mobile",
    [
        "09121234567",     # local format: must be normalised before saving
        "+441234567890",   # valid E.164, but not an Iranian number
        "+98912123456",    # one digit short
        "+982112345678",   # Iranian landline, not a mobile
    ],
)
def test_database_only_stores_iranian_mobiles_with_plus_98(session, model, mobile):
    if model is UserModel:
        row = UserModel(mobile=mobile)
    else:
        row = OtpCodeModel(mobile=mobile, code_hash="x", expires_at=sa.func.now())
    session.add(row)
    with pytest.raises(IntegrityError):
        session.flush()


def test_database_accepts_a_normalised_iranian_mobile(session):
    session.add(UserModel(mobile="+989121234567"))
    session.add(OtpCodeModel(mobile="+989121234567", code_hash="x", expires_at=sa.func.now()))
    session.flush()
