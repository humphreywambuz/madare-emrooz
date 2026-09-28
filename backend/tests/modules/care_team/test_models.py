import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.care_team.domain.enums import ApprovalScope, RiskTag
from app.modules.care_team.infrastructure.models import CareApprovalModel, RiskTagAssignmentModel
from app.modules.identity.domain.enums import UserRole


def test_risk_tag_unique_per_patient(session, make_user):
    patient, doctor = make_user(), make_user(UserRole.DOCTOR)
    for _ in range(2):
        session.add(
            RiskTagAssignmentModel(
                patient_id=patient.id, tag=RiskTag.NEEDS_RHOGAM, added_by_id=doctor.id
            )
        )
    with pytest.raises(IntegrityError):
        session.flush()


def test_one_active_approval_per_scope(session, make_user):
    patient, doctor = make_user(), make_user(UserRole.DOCTOR)
    for _ in range(2):
        session.add(
            CareApprovalModel(
                patient_id=patient.id, approved_by_id=doctor.id, scope=ApprovalScope.PREGNANCY_PLAN
            )
        )
    with pytest.raises(IntegrityError):
        session.flush()
