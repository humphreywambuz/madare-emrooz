"""Bleeding reports, red alerts and the midwife's daily log over HTTP."""
from datetime import timedelta

import sqlalchemy as sa

from app.extensions import db
from app.modules.audit.infrastructure.models import AuditLogModel
from app.modules.identity.domain.enums import UserRole
from app.shared.application.clock import clinic_today

LMP = (clinic_today() - timedelta(weeks=20)).isoformat()


def pregnant_mother(client, signed_in, midwife_id=None):
    mother_id, headers = signed_in()
    client.put(
        "/api/v1/profile",
        json={"first_name": "Sara", "last_name": "Ahmadi", "join_goal": "pregnancy", "reproductive_status": "pregnant"},
        headers=headers,
    )
    client.post("/api/v1/pregnancies", json={"lmp_date": LMP, "conception_type": "natural"}, headers=headers)
    if midwife_id:
        client.put("/api/v1/my-midwife", json={"midwife_id": str(midwife_id)}, headers=headers)
    return mother_id, headers


def listed_midwife(client, signed_in):
    from app.modules.care_team.infrastructure.models import StaffProfileModel

    midwife_id, headers = signed_in(UserRole.MIDWIFE)
    db.session.add(StaffProfileModel(user_id=midwife_id, first_name="Maryam", last_name="Rahimi"))
    db.session.commit()
    return midwife_id, headers


def test_bleeding_alerts_only_her_midwife(client, signed_in):
    midwife_id, midwife = listed_midwife(client, signed_in)
    _, other_midwife = listed_midwife(client, signed_in)
    _, doctor = signed_in(UserRole.DOCTOR)
    _, admin = signed_in(UserRole.ADMIN)
    mother_id, mother = pregnant_mother(client, signed_in, midwife_id)

    report = client.post("/api/v1/daily-logs", json={"has_spotting_or_bleeding": True}, headers=mother)
    assert report.status_code == 201 and report.get_json()["is_red_alert"] is True

    (alert,) = client.get("/api/v1/staff/alerts", headers=midwife).get_json()["items"]
    assert alert["kind"] == "bleeding" and alert["patient_id"] == str(mother_id)
    assert alert["patient_first_name"] == "Sara"
    assert client.get("/api/v1/staff/alerts", headers=other_midwife).get_json()["items"] == []
    assert client.get("/api/v1/staff/alerts", headers=doctor).status_code == 403
    assert client.get("/api/v1/admin/unassigned-alerts", headers=admin).get_json()["items"] == []

    patients = client.get("/api/v1/staff/patients", headers=midwife).get_json()["items"]
    assert patients[0]["open_alerts"] == 1

    # Only her midwife can mark it as seen; then it leaves the inbox.
    assert client.post(f"/api/v1/staff/alerts/{alert['id']}/seen", headers=other_midwife).status_code == 403
    assert client.post(f"/api/v1/staff/alerts/{alert['id']}/seen", headers=midwife).status_code == 204
    assert client.get("/api/v1/staff/alerts", headers=midwife).get_json()["items"] == []
    assert client.post(f"/api/v1/staff/alerts/{alert['id']}/seen", headers=midwife).status_code == 422


def test_no_alert_when_she_reports_no_bleeding(client, signed_in):
    midwife_id, midwife = listed_midwife(client, signed_in)
    _, mother = pregnant_mother(client, signed_in, midwife_id)
    report = client.post("/api/v1/daily-logs", json={"has_spotting_or_bleeding": False}, headers=mother)
    assert report.get_json()["is_red_alert"] is False
    assert client.get("/api/v1/staff/alerts", headers=midwife).get_json()["items"] == []
    assert len(client.get("/api/v1/daily-logs", headers=mother).get_json()["items"]) == 1


def test_alert_before_choosing_a_midwife_goes_to_admins_then_moves_to_her(client, signed_in):
    _, admin = signed_in(UserRole.ADMIN)
    _, mother = pregnant_mother(client, signed_in)
    client.post("/api/v1/daily-logs", json={"has_spotting_or_bleeding": True}, headers=mother)

    (alert,) = client.get("/api/v1/admin/unassigned-alerts", headers=admin).get_json()["items"]
    assert alert["patient_mobile"].startswith("+98935")

    midwife_id, midwife = listed_midwife(client, signed_in)
    client.put("/api/v1/my-midwife", json={"midwife_id": str(midwife_id)}, headers=mother)
    assert client.get("/api/v1/admin/unassigned-alerts", headers=admin).get_json()["items"] == []
    assert len(client.get("/api/v1/staff/alerts", headers=midwife).get_json()["items"]) == 1
    # Now it's hers, so the admin can no longer close it.
    assert client.post(f"/api/v1/staff/alerts/{alert['id']}/seen", headers=admin).status_code == 403


def test_admin_marks_an_unassigned_alert_as_seen(client, signed_in):
    _, admin = signed_in(UserRole.ADMIN)
    _, mother = pregnant_mother(client, signed_in)
    client.post("/api/v1/daily-logs", json={"has_spotting_or_bleeding": True}, headers=mother)
    (alert,) = client.get("/api/v1/admin/unassigned-alerts", headers=admin).get_json()["items"]
    assert client.post(f"/api/v1/staff/alerts/{alert['id']}/seen", headers=admin).status_code == 204
    assert client.get("/api/v1/admin/unassigned-alerts", headers=admin).get_json()["items"] == []


def test_bleeding_needs_an_active_pregnancy(client, signed_in):
    _, mother = signed_in()
    response = client.post("/api/v1/daily-logs", json={"has_spotting_or_bleeding": True}, headers=mother)
    assert response.status_code == 422


def test_mother_cannot_record_vitals(client, signed_in):
    _, mother = pregnant_mother(client, signed_in)
    response = client.post(
        "/api/v1/daily-logs", json={"has_spotting_or_bleeding": False, "systolic_bp": 120}, headers=mother
    )
    assert response.status_code == 422


def test_midwife_records_vitals_for_her_mothers_only(client, signed_in):
    midwife_id, midwife = listed_midwife(client, signed_in)
    _, other_midwife = listed_midwife(client, signed_in)
    _, doctor = signed_in(UserRole.DOCTOR)
    mother_id, _ = pregnant_mother(client, signed_in, midwife_id)
    url = f"/api/v1/staff/patients/{mother_id}/daily-logs"
    vitals = {"systolic_bp": 125, "diastolic_bp": 80, "weight_kg": 68.5, "has_headache": True}

    saved = client.post(url, json=vitals, headers=midwife)
    assert saved.status_code == 201, saved.get_json()
    body = saved.get_json()
    assert body["recorded_by_id"] == str(midwife_id) and body["pregnancy_id"] is not None
    assert body["weight_kg"] == 68.5

    assert client.post(url, json=vitals, headers=other_midwife).status_code == 403
    assert client.post(url, json=vitals, headers=doctor).status_code == 403  # doctors read, midwives write
    assert client.post(url, json={"systolic_bp": 120}, headers=midwife).status_code == 422
    assert client.post(url, json={"systolic_bp": 80, "diastolic_bp": 90}, headers=midwife).status_code == 422
    assert client.post(url, json={}, headers=midwife).status_code == 422

    assert len(client.get(url, headers=doctor).get_json()["items"]) == 1
    assert client.get(url, headers=other_midwife).status_code == 403

    events = [e.value for e in db.session.scalars(sa.select(AuditLogModel.event_type))]
    assert "record_created" in events and "record_viewed" in events
    assert events.count("access_denied") == 2


def test_unknown_patient_is_404(client, signed_in):
    import uuid

    _, midwife = listed_midwife(client, signed_in)
    response = client.get(f"/api/v1/staff/patients/{uuid.uuid4()}/daily-logs", headers=midwife)
    assert response.status_code == 404


def test_raised_alerts_are_audited_with_cause_and_who_was_notified(client, signed_in):
    _, mother_without_midwife = pregnant_mother(client, signed_in)
    midwife_id, _ = listed_midwife(client, signed_in)
    mother_id, mother = pregnant_mother(client, signed_in, midwife_id)
    client.post("/api/v1/daily-logs", json={"has_spotting_or_bleeding": True}, headers=mother_without_midwife)
    client.post("/api/v1/daily-logs", json={"has_spotting_or_bleeding": True}, headers=mother)
    client.post("/api/v1/daily-logs", json={"has_spotting_or_bleeding": False}, headers=mother)

    raised = db.session.scalars(
        sa.select(AuditLogModel).where(AuditLogModel.event_type == "alert_raised").order_by(AuditLogModel.id)
    ).all()
    assert len(raised) == 2
    to_admins, to_midwife = raised
    assert to_admins.details["notified"] == {"role": "admins"}
    assert to_midwife.details["notified"] == {"role": "midwife", "user_id": str(midwife_id)}
    assert to_midwife.details["cause"] == "bleeding" and to_midwife.details["daily_log_id"]
    assert to_midwife.actor_id == mother_id == to_midwife.patient_id
    assert to_midwife.created_at is not None and to_midwife.resource_type == "alert"
