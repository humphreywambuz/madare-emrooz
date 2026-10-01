"""Partner Mode: a QR code that shows the spouse the week and due date, without sign-in."""
import uuid
from datetime import date, timedelta

import sqlalchemy as sa

from app.extensions import db
from app.modules.audit.infrastructure.models import AuditLogModel
from app.modules.pregnancy.domain.partner import parse_partner_token, partner_token

LMP = (date.today() - timedelta(weeks=24, days=3)).isoformat()


def start(client, headers):
    client.post("/api/v1/pregnancies", json={"lmp_date": LMP, "conception_type": "natural"}, headers=headers)


def test_token_is_signed():
    link_id = uuid.uuid4()
    token = partner_token("secret", link_id)
    assert parse_partner_token("secret", token) == link_id
    assert parse_partner_token("other-secret", token) is None
    assert parse_partner_token("secret", token[:-1] + ("A" if token[-1] != "A" else "B")) is None
    assert parse_partner_token("secret", "short") is None


def test_spouse_sees_only_week_and_due_date(app, client, signed_in):
    mother_id, mother = signed_in()
    assert client.post("/api/v1/partner-link", headers=mother).status_code == 422  # no pregnancy yet
    start(client, mother)

    link = client.post("/api/v1/partner-link", headers=mother)
    assert link.status_code == 201
    link = link.get_json()
    assert link["url"].endswith(f"/p/{link['token']}")
    assert client.get("/api/v1/partner-link", headers=mother).get_json()["token"] == link["token"]

    # No sign-in needed.
    view = client.get(f"/api/v1/partner/{link['token']}")
    assert view.status_code == 200
    assert view.get_json() == {**view.get_json(), "gestational_week": 24, "gestational_days": 3}
    assert set(view.get_json()) == {"gestational_week", "gestational_days", "estimated_due_date", "days_until_due"}
    assert view.headers["Cache-Control"] == "no-store"

    page = client.get(f"/p/{link['token']}")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert "هفته ۲۴" in html and "۳ روز" in html and 'dir="rtl"' in html

    viewed = db.session.scalars(
        sa.select(AuditLogModel).where(AuditLogModel.event_type == "partner_link_viewed")
    ).all()
    assert len(viewed) == 2 and viewed[0].patient_id == mother_id and viewed[0].actor_id is None


def test_new_code_replaces_the_old_and_off_means_off(client, signed_in):
    _, mother = signed_in()
    start(client, mother)
    old = client.post("/api/v1/partner-link", headers=mother).get_json()["token"]
    new = client.post("/api/v1/partner-link", headers=mother).get_json()["token"]
    assert old != new
    assert client.get(f"/api/v1/partner/{old}").status_code == 404
    assert client.get(f"/api/v1/partner/{new}").status_code == 200

    assert client.delete("/api/v1/partner-link", headers=mother).status_code == 204
    assert client.get(f"/api/v1/partner/{new}").status_code == 404
    assert client.get(f"/p/{new}").status_code == 404
    assert client.get("/api/v1/partner-link", headers=mother).status_code == 404


def test_link_stops_when_the_pregnancy_ends(client, signed_in):
    _, mother = signed_in()
    start(client, mother)
    token = client.post("/api/v1/partner-link", headers=mother).get_json()["token"]
    client.post("/api/v1/pregnancies/current/end", json={"status": "delivered"}, headers=mother)
    assert client.get(f"/api/v1/partner/{token}").status_code == 404


def test_forged_tokens_are_refused(client):
    assert client.get(f"/api/v1/partner/{uuid.uuid4().hex}{'A' * 22}").status_code == 404
    assert client.get("/p/not-a-token").status_code == 404
