"""Onboarding over HTTP: profile, medical history and the home screen."""
from datetime import timedelta

import sqlalchemy as sa

from app.extensions import db
from app.modules.audit.infrastructure.models import AuditLogModel
from app.shared.application.clock import clinic_today

PROFILE = {
    "first_name": "سارا",
    "last_name": "احمدی",
    "join_goal": "pregnancy",
    "reproductive_status": "pregnant",
    "national_code": "۰۰۱۲۳۴۵۶۷۹",  # Persian digits are accepted
    "birth_date": "1995-06-15",
    "height_cm": 165.5,
    "initial_weight_kg": 60,
    "mother_blood_type": "O-",
    "spouse_blood_type": "A+",
}


def test_new_user_has_no_profile(client, signed_in):
    _, headers = signed_in()
    response = client.get("/api/v1/profile", headers=headers)
    assert response.status_code == 404


def test_create_then_update_profile(client, signed_in):
    user_id, headers = signed_in()
    created = client.put("/api/v1/profile", json=PROFILE, headers=headers)
    assert created.status_code == 201, created.get_json()
    body = created.get_json()
    assert body["national_code"] == "0012345679"
    assert body["spouse_blood_type"] == "A+"
    assert body["rh_incompatibility_risk"] is True
    assert body["height_cm"] == 165.5
    assert body["home"] == "pregnancy"
    assert body["age"] >= 30

    updated = client.put(
        "/api/v1/profile", json={**PROFILE, "reproductive_status": "trying_to_conceive"}, headers=headers
    )
    assert updated.status_code == 200
    assert updated.get_json()["home"] == "trying_to_conceive"
    assert client.get("/api/v1/profile", headers=headers).get_json()["home"] == "trying_to_conceive"

    events = db.session.scalars(sa.select(AuditLogModel.event_type).order_by(AuditLogModel.id)).all()
    assert [e.value for e in events] == ["profile_created", "record_updated"]


def test_home_for_each_path(client, signed_in):
    _, headers = signed_in()
    quick = {"first_name": "Mina", "last_name": "Karimi"}
    cases = [
        ({"join_goal": "pregnancy", "reproductive_status": "postpartum"}, "postpartum"),
        ({"join_goal": "fitness"}, "fitness"),
        ({"join_goal": "rehabilitation"}, "rehabilitation"),
    ]
    for extra, home in cases:
        response = client.put("/api/v1/profile", json={**quick, **extra}, headers=headers)
        assert response.get_json()["home"] == home


def test_profile_validation(client, signed_in):
    _, headers = signed_in()

    def put(**changes):
        return client.put("/api/v1/profile", json={**PROFILE, **changes}, headers=headers)

    assert put(national_code="0012345678").status_code == 422  # wrong check digit
    assert put(national_code="1111111111").status_code == 422
    assert put(reproductive_status=None).status_code == 422  # pregnancy path needs a status
    assert put(birth_date=(clinic_today() + timedelta(days=1)).isoformat()).status_code == 422
    assert put(height_cm=300).status_code == 422
    assert put(unknown_field=1).status_code == 422


def test_national_code_belongs_to_one_person(client, signed_in):
    _, first = signed_in()
    _, second = signed_in()
    assert client.put("/api/v1/profile", json=PROFILE, headers=first).status_code == 201
    response = client.put("/api/v1/profile", json=PROFILE, headers=second)
    assert response.status_code == 409


def test_medical_history(client, signed_in):
    _, headers = signed_in()
    assert client.get("/api/v1/medical-history", headers=headers).status_code == 404
    saved = client.put(
        "/api/v1/medical-history",
        json={"miscarriage_count": 1, "has_diabetes": False, "spouse_has_diabetes": True},
        headers=headers,
    )
    assert saved.status_code == 201
    body = client.get("/api/v1/medical-history", headers=headers).get_json()
    assert body["miscarriage_count"] == 1 and body["has_diabetes"] is False
    assert body["has_hypertension"] is None  # not answered
    assert client.put("/api/v1/medical-history", json={"miscarriage_count": -1}, headers=headers).status_code == 422


def test_delivery_switches_home_to_postpartum(client, signed_in):
    _, headers = signed_in()
    client.put("/api/v1/profile", json=PROFILE, headers=headers)
    lmp = (clinic_today() - timedelta(weeks=39)).isoformat()
    client.post("/api/v1/pregnancies", json={"lmp_date": lmp, "conception_type": "natural"}, headers=headers)
    ended = client.post("/api/v1/pregnancies/current/end", json={"status": "delivered"}, headers=headers)
    assert ended.status_code == 200
    profile = client.get("/api/v1/profile", headers=headers).get_json()
    assert profile["reproductive_status"] == "postpartum"
    assert profile["home"] == "postpartum"
