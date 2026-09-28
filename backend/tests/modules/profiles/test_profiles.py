from datetime import date

from app.modules.profiles.domain.enums import BloodType, JoinGoal
from app.modules.profiles.domain.rules import age_on, rh_incompatibility_risk
from app.modules.profiles.infrastructure.models import MedicalHistoryModel, ProfileModel


def test_age_on():
    assert age_on(date(1995, 6, 15), date(2026, 6, 14)) == 30
    assert age_on(date(1995, 6, 15), date(2026, 6, 15)) == 31


def test_rh_incompatibility_risk():
    assert rh_incompatibility_risk(BloodType.O_NEG, BloodType.A_POS) is True
    assert rh_incompatibility_risk(BloodType.O_NEG, BloodType.A_NEG) is False
    assert rh_incompatibility_risk(BloodType.O_POS, BloodType.A_POS) is False
    assert rh_incompatibility_risk(None, BloodType.A_POS) is False


def test_profile_and_medical_history(session, make_user):
    user = make_user()
    profile = ProfileModel(
        user_id=user.id,
        first_name="Sara",
        last_name="Ahmadi",
        national_code="0012345678",
        birth_date=date(1995, 6, 15),
        mother_blood_type=BloodType.O_NEG,
        father_blood_type=BloodType.A_POS,
        join_goal=JoinGoal.PREGNANCY,
    )
    history = MedicalHistoryModel(user_id=user.id, miscarriage_count=1, has_diabetes=False)
    session.add_all([profile, history])
    session.flush()

    assert profile.rh_incompatibility_risk is True
    assert profile.age == age_on(date(1995, 6, 15), date.today())
    assert history.has_hypertension is None  # not answered
