"""Staff accounts, choosing a midwife and patient lists over HTTP."""
import sqlalchemy as sa

from app.extensions import db
from app.modules.audit.infrastructure.models import AuditLogModel
from app.modules.identity.domain.enums import UserRole
from tests.conftest import auth_headers


def create_staff(client, admin, role="midwife", mobile="09120000001", **extra):
    body = {"mobile": mobile, "role": role, "first_name": "Maryam", "last_name": "Rahimi", **extra}
    response = client.post("/api/v1/admin/staff", json=body, headers=admin)
    assert response.status_code == 201, response.get_json()
    return response.get_json()


def test_admin_creates_staff_who_can_then_sign_in(app, client, signed_in):
    _, admin = signed_in(UserRole.ADMIN)
    staff = create_staff(client, admin, bio="۱۰ سال سابقه")
    assert staff["mobile"] == "+989120000001" and staff["role"] == "midwife"
    assert staff["is_listed"] is True and staff["is_active"] is True

    # The midwife signs in with an SMS code like everyone else and keeps her role.
    client.post("/api/v1/auth/otp/request", json={"mobile": "09120000001"})
    code = app.extensions["sms_outbox"][-1][1].split()[-1]
    tokens = client.post("/api/v1/auth/otp/verify", json={"mobile": "09120000001", "code": code}).get_json()
    assert tokens["user"]["role"] == "midwife" and tokens["is_new_user"] is False

    listed = client.get("/api/v1/admin/staff", headers=admin).get_json()["items"]
    assert staff["user_id"] in [s["user_id"] for s in listed]


def test_only_admins_manage_staff_and_mobiles_are_unique(client, signed_in):
    _, admin = signed_in(UserRole.ADMIN)
    _, mother = signed_in()
    _, midwife = signed_in(UserRole.MIDWIFE)
    body = {"mobile": "09120000002", "role": "doctor", "first_name": "A", "last_name": "B"}
    assert client.post("/api/v1/admin/staff", json=body, headers=mother).status_code == 403
    assert client.post("/api/v1/admin/staff", json=body, headers=midwife).status_code == 403
    assert client.post("/api/v1/admin/staff", json=body, headers=admin).status_code == 201
    assert client.post("/api/v1/admin/staff", json=body, headers=admin).status_code == 409
    assert client.post("/api/v1/admin/staff", json={**body, "mobile": "09120000003", "role": "user"}, headers=admin).status_code == 422


def test_mother_chooses_and_changes_her_midwife(app, client, signed_in):
    _, admin = signed_in(UserRole.ADMIN)
    first = create_staff(client, admin, mobile="09120000011")
    second = create_staff(client, admin, mobile="09120000012", first_name="Leila")
    hidden = create_staff(client, admin, mobile="09120000013", is_listed=False)
    doctor = create_staff(client, admin, role="doctor", mobile="09120000014")
    mother_id, mother = signed_in()

    options = client.get("/api/v1/midwives", headers=mother).get_json()["items"]
    assert {o["id"] for o in options} == {first["user_id"], second["user_id"]}
    assert "mobile" not in options[0]

    assert client.get("/api/v1/my-midwife", headers=mother).get_json() == {"midwife": None}
    chosen = client.put("/api/v1/my-midwife", json={"midwife_id": first["user_id"]}, headers=mother)
    assert chosen.status_code == 200 and chosen.get_json()["midwife"]["id"] == first["user_id"]
    # Unlisted midwives and doctors can't be chosen.
    for other in (hidden, doctor):
        assert client.put("/api/v1/my-midwife", json={"midwife_id": other["user_id"]}, headers=mother).status_code == 422

    first_headers = auth_headers(app, first["user_id"], UserRole.MIDWIFE)
    second_headers = auth_headers(app, second["user_id"], UserRole.MIDWIFE)
    assert [p["id"] for p in client.get("/api/v1/staff/patients", headers=first_headers).get_json()["items"]] == [str(mother_id)]

    client.put("/api/v1/my-midwife", json={"midwife_id": second["user_id"]}, headers=mother)
    assert client.get("/api/v1/staff/patients", headers=first_headers).get_json()["items"] == []
    assert len(client.get("/api/v1/staff/patients", headers=second_headers).get_json()["items"]) == 1
    assert client.get("/api/v1/my-midwife", headers=mother).get_json()["midwife"]["first_name"] == "Leila"

    events = db.session.scalars(sa.select(AuditLogModel.event_type)).all()
    assert sum(e.value == "midwife_chosen" for e in events) == 2


def test_staff_cannot_choose_a_midwife(client, signed_in):
    _, doctor = signed_in(UserRole.DOCTOR)
    assert client.get("/api/v1/midwives", headers=doctor).status_code == 403


def test_doctors_see_every_mother(client, signed_in):
    _, doctor = signed_in(UserRole.DOCTOR)
    signed_in()
    signed_in()
    signed_in(UserRole.MIDWIFE)  # staff are not patients
    patients = client.get("/api/v1/staff/patients", headers=doctor).get_json()["items"]
    assert len(patients) == 2 and patients[0]["open_alerts"] == 0


def test_doctors_see_only_their_mothers_when_scope_is_assigned(app, client, signed_in):
    _, doctor = signed_in(UserRole.DOCTOR)
    signed_in()
    app.config["DOCTOR_PATIENT_SCOPE"] = "assigned"
    try:
        assert client.get("/api/v1/staff/patients", headers=doctor).get_json()["items"] == []
    finally:
        app.config["DOCTOR_PATIENT_SCOPE"] = "all"


def test_deactivating_a_midwife_frees_her_mothers(app, client, signed_in):
    _, admin = signed_in(UserRole.ADMIN)
    midwife = create_staff(client, admin)
    _, mother = signed_in()
    client.put("/api/v1/my-midwife", json={"midwife_id": midwife["user_id"]}, headers=mother)

    response = client.patch(f"/api/v1/admin/staff/{midwife['user_id']}", json={"is_active": False}, headers=admin)
    assert response.status_code == 200 and response.get_json()["is_active"] is False
    assert client.get("/api/v1/my-midwife", headers=mother).get_json() == {"midwife": None}
    assert client.get("/api/v1/midwives", headers=mother).get_json()["items"] == []
    # Her old token stops working at once.
    headers = auth_headers(app, midwife["user_id"], UserRole.MIDWIFE)
    assert client.get("/api/v1/staff/patients", headers=headers).status_code == 401


def test_create_admin_command(app, client):
    result = app.test_cli_runner().invoke(
        args=["create-admin", "09121112233", "--first-name", "Ali", "--last-name", "Admin"]
    )
    assert result.exit_code == 0, result.output
    assert "+989121112233" in result.output
