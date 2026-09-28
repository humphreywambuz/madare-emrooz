from app.modules.identity.domain.enums import UserRole
from app.modules.monitoring.infrastructure.models import DailyLogModel


def test_bleeding_raises_red_alert(session, make_user):
    user = make_user()
    midwife = make_user(UserRole.MIDWIFE)
    calm = DailyLogModel(patient_id=user.id, recorded_by_id=midwife.id, systolic_bp=120)
    bleeding = DailyLogModel(patient_id=user.id, recorded_by_id=user.id, has_spotting_or_bleeding=True)
    session.add_all([calm, bleeding])
    session.flush()
    session.refresh(calm)
    session.refresh(bleeding)

    assert calm.is_red_alert is False
    assert bleeding.is_red_alert is True
