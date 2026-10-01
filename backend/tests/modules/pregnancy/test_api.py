from datetime import date, timedelta

LMP = (date.today() - timedelta(weeks=10)).isoformat()


def test_requires_sign_in(client):
    response = client.get("/api/v1/pregnancies/current")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "unauthenticated"


def test_rejects_invalid_token(client):
    response = client.get(
        "/api/v1/pregnancies/current", headers={"Authorization": "Bearer not-a-token"}
    )
    assert response.status_code == 401


def test_start_get_and_end_pregnancy(client, signed_in):
    _, headers = signed_in()

    created = client.post(
        "/api/v1/pregnancies",
        json={"lmp_date": LMP, "conception_type": "natural"},
        headers=headers,
    )
    assert created.status_code == 201
    body = created.get_json()
    assert body["gestational_week"] == 10
    assert body["status"] == "active"

    current = client.get("/api/v1/pregnancies/current", headers=headers)
    assert current.status_code == 200
    assert current.get_json()["id"] == body["id"]

    duplicate = client.post(
        "/api/v1/pregnancies", json={"lmp_date": LMP, "conception_type": "natural"}, headers=headers
    )
    assert duplicate.status_code == 409

    ended = client.post("/api/v1/pregnancies/current/end", json={"status": "delivered"}, headers=headers)
    assert ended.status_code == 200
    assert client.get("/api/v1/pregnancies/current", headers=headers).status_code == 404


def test_validation_errors(client, signed_in):
    _, headers = signed_in()
    bad_body = client.post(
        "/api/v1/pregnancies", json={"lmp_date": LMP, "conception_type": "magic"}, headers=headers
    )
    assert bad_body.status_code == 422
    assert bad_body.get_json()["error"]["details"]["fields"][0]["field"] == "conception_type"

    future = (date.today() + timedelta(days=3)).isoformat()
    bad_rule = client.post(
        "/api/v1/pregnancies", json={"lmp_date": future, "conception_type": "natural"}, headers=headers
    )
    assert bad_rule.status_code == 422


def test_dates_are_returned_as_iso_8601(client, signed_in):
    _, headers = signed_in()
    body = client.post(
        "/api/v1/pregnancies", json={"lmp_date": LMP, "conception_type": "natural"}, headers=headers
    ).get_json()
    assert body["lmp_date"] == LMP
    assert date.fromisoformat(body["estimated_due_date"]) == date.fromisoformat(LMP) + timedelta(days=280)


def test_concurrent_duplicate_start_is_a_conflict(client, signed_in, monkeypatch):
    """Two requests can both pass the 'already active?' check; the database
    constraint then rejects the second insert, which must surface as 409, not 500."""
    from app.modules.pregnancy.infrastructure.repository import SqlAlchemyPregnancyRepository

    _, headers = signed_in()
    payload = {"lmp_date": LMP, "conception_type": "natural"}
    assert client.post("/api/v1/pregnancies", json=payload, headers=headers).status_code == 201

    monkeypatch.setattr(SqlAlchemyPregnancyRepository, "get_active_for_user", lambda self, user_id: None)
    response = client.post("/api/v1/pregnancies", json=payload, headers=headers)
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "conflict"


def _audit(event):
    import sqlalchemy as sa

    from app.extensions import db
    from app.modules.audit.infrastructure.models import AuditLogModel

    return db.session.scalars(
        sa.select(AuditLogModel).where(AuditLogModel.event_type == event).order_by(AuditLogModel.id)
    ).all()


def test_mother_corrects_her_lmp_without_ending_the_pregnancy(client, signed_in):
    _, headers = signed_in()
    created = client.post("/api/v1/pregnancies", json={"lmp_date": LMP, "conception_type": "natural"}, headers=headers).get_json()
    fixed_lmp = (date.today() - timedelta(weeks=12)).isoformat()
    fixed = client.patch("/api/v1/pregnancies/current", json={"lmp_date": fixed_lmp, "care_provider_type": "midwife"}, headers=headers)
    assert fixed.status_code == 200, fixed.get_json()
    body = fixed.get_json()
    assert body["id"] == created["id"] and body["status"] == "active"
    assert body["gestational_week"] == 12 and body["due_date_source"] == "lmp"
    assert body["care_provider_type"] == "midwife"
    (event,) = _audit("record_updated")
    assert event.details["changed"] == ["care_provider_type", "lmp_date"]

    future = (date.today() + timedelta(days=1)).isoformat()
    assert client.patch("/api/v1/pregnancies/current", json={"lmp_date": future}, headers=headers).status_code == 422
    assert client.patch("/api/v1/pregnancies/current", json={"lmp_date": None}, headers=headers).status_code == 422
    assert client.patch("/api/v1/pregnancies/current", json={"status": "ended"}, headers=headers).status_code == 422


def test_care_team_corrects_the_due_date_and_it_then_wins(client, signed_in):
    from tests.modules.monitoring.test_api import listed_midwife, pregnant_mother

    midwife_id, midwife = listed_midwife(client, signed_in)
    _, other_midwife = listed_midwife(client, signed_in)
    mother_id, mother = pregnant_mother(client, signed_in, midwife_id)  # 20 weeks by LMP
    url = f"/api/v1/staff/patients/{mother_id}/pregnancy/due-date"
    ultrasound = (date.today() + timedelta(weeks=19)).isoformat()  # 21 weeks today

    assert client.put(url, json={"estimated_due_date": ultrasound}, headers=other_midwife).status_code == 403
    corrected = client.put(url, json={"estimated_due_date": ultrasound, "reason": "NT scan"}, headers=midwife)
    assert corrected.status_code == 200, corrected.get_json()
    body = corrected.get_json()
    assert body["estimated_due_date"] == ultrasound and body["gestational_week"] == 21
    assert body["due_date_source"] == "clinician" and body["due_date_corrected_at"]
    (event,) = _audit("record_updated")
    assert event.details["reason"] == "NT scan" and event.details["due_date"]["to"] == ultrasound

    # Her later LMP fix keeps the clinician's due date.
    client.patch("/api/v1/pregnancies/current", json={"lmp_date": (date.today() - timedelta(weeks=18)).isoformat()}, headers=mother)
    assert client.get("/api/v1/pregnancies/current", headers=mother).get_json()["estimated_due_date"] == ultrasound

    too_far = (date.today() + timedelta(weeks=45)).isoformat()
    assert client.put(url, json={"estimated_due_date": too_far}, headers=midwife).status_code == 422


def test_due_date_correction_needs_an_active_pregnancy(client, signed_in):
    from tests.modules.monitoring.test_api import listed_midwife

    midwife_id, midwife = listed_midwife(client, signed_in)
    mother_id, mother = signed_in()
    client.put("/api/v1/my-midwife", json={"midwife_id": str(midwife_id)}, headers=mother)
    url = f"/api/v1/staff/patients/{mother_id}/pregnancy/due-date"
    assert client.put(url, json={"estimated_due_date": date.today().isoformat()}, headers=midwife).status_code == 404
    assert client.patch("/api/v1/pregnancies/current", json={"conception_type": "assisted"}, headers=mother).status_code == 404
