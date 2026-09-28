from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError, StatementError

from app.models import (
    AuditLog,
    CareApproval,
    DailyLog,
    MedicalDocument,
    MedicalHistory,
    Pregnancy,
    Profile,
    RehabProfile,
    RiskTagAssignment,
    User,
)
from app.models.enums import (
    ApprovalScope,
    AuditEventType,
    BloodType,
    ConceptionType,
    DocumentType,
    JoinGoal,
    RehabSubcategory,
    RiskTag,
    UserRole,
)


def make_user(session, mobile="+989121234567", role=UserRole.USER):
    user = User(mobile=mobile, role=role)
    session.add(user)
    session.flush()
    return user


def make_pregnancy(user, lmp=date(2026, 1, 1)):
    return Pregnancy(
        user=user,
        lmp_date=lmp,
        conception_type=ConceptionType.NATURAL,
        estimated_due_date=Pregnancy.calculate_due_date(lmp),
    )


def test_user_defaults(session):
    user = make_user(session)
    session.refresh(user)
    assert user.role is UserRole.USER
    assert user.is_active is True
    assert user.created_at is not None


def test_mobile_must_be_e164(session):
    session.add(User(mobile="09121234567"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_invalid_enum_value_is_rejected(session):
    session.add(User(mobile="+989121234567", role="superuser"))
    with pytest.raises(StatementError):
        session.flush()


def test_profile_and_medical_history(session):
    user = make_user(session)
    user.profile = Profile(
        first_name="Sara",
        last_name="Ahmadi",
        national_code="0012345678",
        birth_date=date(1995, 6, 15),
        mother_blood_type=BloodType.O_NEG,
        father_blood_type=BloodType.A_POS,
        join_goal=JoinGoal.PREGNANCY,
    )
    user.medical_history = MedicalHistory(miscarriage_count=1, has_diabetes=False)
    session.flush()

    assert user.profile.rh_incompatibility_risk is True
    assert user.profile.age == date.today().year - 1995 - (
        (date.today().month, date.today().day) < (6, 15)
    )
    assert user.medical_history.has_hypertension is None  # not answered


def test_due_date_and_gestational_week():
    lmp = date(2026, 1, 1)
    assert Pregnancy.calculate_due_date(lmp) == date(2026, 10, 8)
    assert Pregnancy.calculate_due_date(lmp, cycle_length_days=35) == date(2026, 10, 15)

    pregnancy = Pregnancy(lmp_date=lmp, estimated_due_date=Pregnancy.calculate_due_date(lmp))
    assert pregnancy.gestational_week(on=lmp + timedelta(weeks=12, days=3)) == 12


def test_only_one_active_pregnancy_per_user(session):
    user = make_user(session)
    session.add(make_pregnancy(user))
    session.flush()
    session.add(make_pregnancy(user, lmp=date(2026, 2, 1)))
    with pytest.raises(IntegrityError):
        session.flush()


def test_bleeding_raises_red_alert(session):
    user = make_user(session)
    midwife = make_user(session, mobile="+989351112233", role=UserRole.MIDWIFE)
    calm = DailyLog(patient_id=user.id, recorded_by_id=midwife.id, systolic_bp=120)
    bleeding = DailyLog(patient_id=user.id, recorded_by_id=user.id, has_spotting_or_bleeding=True)
    session.add_all([calm, bleeding])
    session.flush()
    session.refresh(calm)
    session.refresh(bleeding)

    assert calm.is_red_alert is False
    assert bleeding.is_red_alert is True


def test_medical_document(session):
    user = make_user(session)
    doc = MedicalDocument(
        patient_id=user.id,
        uploaded_by_id=user.id,
        document_type=DocumentType.ULTRASOUND,
        storage_key="patients/abc/ultrasound-1.pdf",
        original_filename="ultrasound.pdf",
        content_type="application/pdf",
        file_size_bytes=2048,
        fetal_heart_rate_bpm=140,
    )
    session.add(doc)
    session.flush()
    assert doc.id is not None


def test_risk_tag_unique_per_patient(session):
    patient = make_user(session)
    doctor = make_user(session, mobile="+989351112233", role=UserRole.DOCTOR)
    for _ in range(2):
        session.add(
            RiskTagAssignment(patient_id=patient.id, tag=RiskTag.NEEDS_RHOGAM, added_by_id=doctor.id)
        )
    with pytest.raises(IntegrityError):
        session.flush()


def test_rehab_pain_level_range(session):
    user = make_user(session)
    user.rehab_profile = RehabProfile(
        subcategory=RehabSubcategory.INJURY_CORRECTION,
        pain_level=11,
        had_related_surgery=False,
        uses_pain_medication=False,
    )
    with pytest.raises(IntegrityError):
        session.flush()


def test_rehab_surgery_name_required(session):
    user = make_user(session)
    user.rehab_profile = RehabProfile(
        subcategory=RehabSubcategory.POSTPARTUM_RECOVERY,
        pain_level=4,
        had_related_surgery=True,
        uses_pain_medication=False,
    )
    with pytest.raises(IntegrityError):
        session.flush()


def test_rehab_unlocks_after_visit_and_approval(session):
    patient = make_user(session)
    doctor = make_user(session, mobile="+989351112233", role=UserRole.DOCTOR)
    patient.rehab_profile = RehabProfile(
        subcategory=RehabSubcategory.YOGA_MEDITATION,
        pain_level=3,
        had_related_surgery=False,
        uses_pain_medication=False,
    )
    session.flush()
    assert patient.rehab_profile.is_advanced_locked is True

    patient.rehab_profile.specialist_visit_completed = True
    assert patient.rehab_profile.is_advanced_locked is True  # still needs approval

    approval = CareApproval(
        patient=patient, approved_by_id=doctor.id, scope=ApprovalScope.REHABILITATION_PLAN
    )
    session.add(approval)
    session.flush()
    assert patient.rehab_profile.is_advanced_locked is False

    approval.revoked_at = datetime.now(timezone.utc)
    assert patient.rehab_profile.is_advanced_locked is True


def test_one_active_approval_per_scope(session):
    patient = make_user(session)
    doctor = make_user(session, mobile="+989351112233", role=UserRole.DOCTOR)
    for _ in range(2):
        session.add(
            CareApproval(
                patient_id=patient.id, approved_by_id=doctor.id, scope=ApprovalScope.PREGNANCY_PLAN
            )
        )
    with pytest.raises(IntegrityError):
        session.flush()


def test_audit_log_survives_without_foreign_keys(session):
    log = AuditLog(
        actor_id=None,
        event_type=AuditEventType.ACCESS_DENIED,
        ip_address="192.0.2.10",
        details={"path": "/patients/123"},
    )
    session.add(log)
    session.flush()
    assert log.id is not None
