"""The staff panel's summary card, full record, notes, tags and approvals."""
import sqlalchemy as sa

from app.extensions import db
from app.modules.audit.infrastructure.models import AuditLogModel
from app.modules.care_team.domain.enums import RiskTag
from app.modules.care_team.domain.risk import PatientFacts, derive_risk_tags
from app.modules.identity.domain.enums import UserRole
from tests.modules.monitoring.test_api import listed_midwife, pregnant_mother
from tests.modules.rehabilitation.test_api import POSTPARTUM


def test_derived_tags():
    assert derive_risk_tags(PatientFacts()) == set()
    facts = PatientFacts(rh_incompatibility_risk=True, miscarriage_count=2, has_diabetes=False, has_infectious_disease=True)
    assert derive_risk_tags(facts) == {RiskTag.NEEDS_RHOGAM, RiskTag.MISCARRIAGE_HISTORY, RiskTag.INFECTIOUS_DISEASE}


def setup_mother(client, signed_in):
    midwife_id, midwife = listed_midwife(client, signed_in)
    mother_id, mother = pregnant_mother(client, signed_in, midwife_id)
    client.put(
        "/api/v1/profile",
        json={"first_name": "Sara", "last_name": "Ahmadi", "join_goal": "pregnancy",
              "reproductive_status": "pregnant", "mother_blood_type": "A-", "spouse_blood_type": "O+"},
        headers=mother,
    )
    client.put("/api/v1/medical-history", json={"miscarriage_count": 1, "has_thyroid_disorder": True}, headers=mother)
    return mother_id, mother, midwife


def test_summary_card_shows_red_flags_from_her_record(client, signed_in):
    mother_id, _, midwife = setup_mother(client, signed_in)
    card = client.get(f"/api/v1/staff/patients/{mother_id}/summary", headers=midwife)
    assert card.status_code == 200
    body = card.get_json()
    assert body["patient"]["first_name"] == "Sara" and body["patient"]["gestational_week"] == 20
    assert body["patient"]["midwife"]["first_name"] == "Maryam"
    assert {(t["tag"], t["source"]) for t in body["risk_tags"]} == {
        ("needs_rhogam", "record"), ("miscarriage_history", "record"), ("thyroid", "record"),
    }


def test_staff_add_and_remove_tags(client, signed_in):
    mother_id, _, midwife = setup_mother(client, signed_in)
    url = f"/api/v1/staff/patients/{mother_id}/risk-tags"
    assert client.post(url, json={"tag": "anemia", "note": "Hb 9.8"}, headers=midwife).status_code == 201
    assert client.post(url, json={"tag": "anemia"}, headers=midwife).status_code == 409
    tags = client.get(f"/api/v1/staff/patients/{mother_id}/summary", headers=midwife).get_json()["risk_tags"]
    assert {"tag": "anemia", "source": "staff", "note": "Hb 9.8"}.items() <= next(t for t in tags if t["tag"] == "anemia").items()
    assert client.delete(f"{url}/anemia", headers=midwife).status_code == 204
    assert client.delete(f"{url}/anemia", headers=midwife).status_code == 404
    assert client.delete(f"{url}/not-a-tag", headers=midwife).status_code == 404


def test_full_record_is_audited_and_limited_to_her_care_team(client, signed_in):
    mother_id, mother, midwife = setup_mother(client, signed_in)
    _, other_midwife = listed_midwife(client, signed_in)
    _, doctor = signed_in(UserRole.DOCTOR)
    _, admin = signed_in(UserRole.ADMIN)
    client.post("/api/v1/daily-logs", json={"has_spotting_or_bleeding": True}, headers=mother)
    client.post(f"/api/v1/staff/patients/{mother_id}/notes", json={"body": "Ultrasound next week."}, headers=doctor)

    record = client.get(f"/api/v1/staff/patients/{mother_id}/record", headers=midwife)
    assert record.status_code == 200
    body = record.get_json()
    assert body["profile"]["spouse_blood_type"] == "O+"
    assert body["medical_history"]["miscarriage_count"] == 1
    assert body["pregnancy"]["gestational_week"] == 20
    assert body["daily_logs"][0]["is_red_alert"] is True
    assert body["notes"][0]["body"] == "Ultrasound next week." and body["notes"][0]["author_role"] == "doctor"
    assert body["fitness_profile"] is None and body["rehab_profile"] is None

    assert client.get(f"/api/v1/staff/patients/{mother_id}/record", headers=doctor).status_code == 200
    assert client.get(f"/api/v1/staff/patients/{mother_id}/record", headers=other_midwife).status_code == 403
    assert client.get(f"/api/v1/staff/patients/{mother_id}/record", headers=admin).status_code == 403
    assert client.get(f"/api/v1/staff/patients/{mother_id}/record", headers=mother).status_code == 403

    events = db.session.scalars(
        sa.select(AuditLogModel.event_type).where(AuditLogModel.patient_id == mother_id)
    ).all()
    events = [e.value for e in events]
    assert events.count("record_viewed") == 2 and events.count("access_denied") == 1


def test_doctor_approval_unlocks_rehabilitation(client, signed_in):
    midwife_id, midwife = listed_midwife(client, signed_in)
    _, doctor = signed_in(UserRole.DOCTOR)
    mother_id, mother = signed_in()
    client.put("/api/v1/my-midwife", json={"midwife_id": str(midwife_id)}, headers=mother)
    client.put("/api/v1/rehab-profile", json=POSTPARTUM, headers=mother)
    approvals = f"/api/v1/staff/patients/{mother_id}/approvals"
    plan = {"scope": "rehabilitation_plan"}

    assert client.post(approvals, json=plan, headers=midwife).status_code == 403  # only doctors approve
    assert client.post(approvals, json=plan, headers=doctor).status_code == 201
    assert client.post(approvals, json=plan, headers=doctor).status_code == 409
    # Approval alone isn't enough: the specialist visit is needed too.
    assert client.get("/api/v1/rehab-profile", headers=mother).get_json()["is_advanced_locked"] is True
    client.post(f"/api/v1/staff/patients/{mother_id}/rehab-profile/specialist-visit", headers=midwife)
    assert client.get("/api/v1/rehab-profile", headers=mother).get_json()["is_advanced_locked"] is False

    assert client.delete(f"{approvals}/rehabilitation_plan", headers=doctor).status_code == 204
    assert client.get("/api/v1/rehab-profile", headers=mother).get_json()["is_advanced_locked"] is True
    history = client.get(f"/api/v1/staff/patients/{mother_id}/record", headers=doctor).get_json()["approvals"]
    assert len(history) == 1 and history[0]["is_active"] is False


def test_notes_need_a_body(client, signed_in):
    mother_id, _, midwife = setup_mother(client, signed_in)
    url = f"/api/v1/staff/patients/{mother_id}/notes"
    assert client.post(url, json={"body": "   "}, headers=midwife).status_code == 422
    assert client.post(url, json={}, headers=midwife).status_code == 422
