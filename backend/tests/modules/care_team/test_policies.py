import uuid

from app.modules.care_team.domain.enums import DoctorPatientScope
from app.modules.care_team.domain.policies import alert_goes_to_admins, can_open_record

ME, OTHER = uuid.uuid4(), uuid.uuid4()


def opens(role, *, midwife=None, doctor=None, scope=DoctorPatientScope.ALL):
    return can_open_record(
        viewer_id=ME, viewer_role=role, midwife_id=midwife, doctor_id=doctor, doctor_scope=scope
    )


def test_midwife_sees_only_mothers_who_chose_her():
    assert opens("midwife", midwife=ME)
    assert not opens("midwife", midwife=OTHER)
    assert not opens("midwife")


def test_doctor_sees_every_mother_in_phase_1_and_only_their_own_in_phase_2():
    assert opens("doctor")
    assert opens("doctor", doctor=OTHER)
    assigned = DoctorPatientScope.ASSIGNED
    assert opens("doctor", doctor=ME, scope=assigned)
    assert not opens("doctor", doctor=OTHER, scope=assigned)
    assert not opens("doctor", scope=assigned)


def test_admins_and_mothers_do_not_open_records():
    assert not opens("admin", midwife=ME)
    assert not opens("user", midwife=ME)


def test_alerts_without_a_midwife_go_to_admins():
    assert alert_goes_to_admins(None)
    assert not alert_goes_to_admins(ME)
