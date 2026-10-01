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
