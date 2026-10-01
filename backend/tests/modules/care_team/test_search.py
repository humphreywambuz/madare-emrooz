"""Searching and paging the staff patient list."""
from app.modules.care_team.domain.search import PatientSearch, parse_patient_search
from app.modules.identity.domain.enums import UserRole


def test_parse_patient_search():
    assert parse_patient_search(None) is None
    assert parse_patient_search("   ") is None
    assert parse_patient_search("۰۹۱۲ ۱۲۳") == PatientSearch(digits="912123")
    assert parse_patient_search("+98 912") == PatientSearch(digits="98912")
    assert parse_patient_search("0098912") == PatientSearch(digits="912")
    assert parse_patient_search("علي  Ahmadi") == PatientSearch(words=("علی", "ahmadi"))


def mother(client, signed_in, first, last, national_code=None):
    user_id, headers = signed_in()
    body = {"first_name": first, "last_name": last, "join_goal": "fitness"}
    if national_code:
        body["national_code"] = national_code
    assert client.put("/api/v1/profile", json=body, headers=headers).status_code == 201
    return str(user_id)


def ids(client, doctor, **params):
    return [p["id"] for p in client.get("/api/v1/staff/patients", query_string=params, headers=doctor).get_json()["items"]]


def test_search_by_name_mobile_and_national_code(app, client, signed_in):
    from app.extensions import db
    from app.modules.identity.infrastructure.models import UserModel

    _, doctor = signed_in(UserRole.DOCTOR)
    sara = mother(client, signed_in, "سارا", "احمدی", national_code="0012345679")
    zahra = mother(client, signed_in, "زهرا", "كريمي")  # typed with Arabic ك and ي
    mina = mother(client, signed_in, "Mina", "Ahmadi")
    mobile = db.session.get(UserModel, sara).mobile  # +98935…

    assert set(ids(client, doctor, q="احمدی")) == {sara}
    assert set(ids(client, doctor, q="AHMADI")) == {mina}
    assert set(ids(client, doctor, q="سارا احمدی")) == {sara}
    assert set(ids(client, doctor, q="کریمی")) == {zahra}  # Persian spelling finds the Arabic one
    assert set(ids(client, doctor, q="0" + mobile[3:])) == {sara}  # local form 0935…
    assert set(ids(client, doctor, q=mobile[3:].translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")))) == {sara}
    assert set(ids(client, doctor, q="00123")) == {sara}  # national code
    assert ids(client, doctor, q="%") == []  # wildcards are literal
    assert ids(client, doctor, q="nobody") == []


def test_paging(client, signed_in):
    _, doctor = signed_in(UserRole.DOCTOR)
    for i in range(5):
        mother(client, signed_in, f"M{i}", "Test")
    first = client.get("/api/v1/staff/patients?per_page=2", headers=doctor).get_json()
    assert first["total"] == 5 and first["page"] == 1 and first["per_page"] == 2 and len(first["items"]) == 2
    last = client.get("/api/v1/staff/patients?per_page=2&page=3", headers=doctor).get_json()
    assert len(last["items"]) == 1
    every = {p["id"] for page in (1, 2, 3) for p in client.get(f"/api/v1/staff/patients?per_page=2&page={page}", headers=doctor).get_json()["items"]}
    assert len(every) == 5
    assert client.get("/api/v1/staff/patients?per_page=500", headers=doctor).status_code == 422
    assert client.get("/api/v1/staff/patients?page=0", headers=doctor).status_code == 422


def test_staff_me(client, signed_in):
    _, admin = signed_in(UserRole.ADMIN)
    body = {"mobile": "09120000099", "role": "midwife", "first_name": "Maryam", "last_name": "Rahimi"}
    staff = client.post("/api/v1/admin/staff", json=body, headers=admin).get_json()
    from tests.conftest import auth_headers
    from flask import current_app

    me = client.get("/api/v1/staff/me", headers=auth_headers(current_app, staff["user_id"], UserRole.MIDWIFE))
    assert me.status_code == 200 and me.get_json()["first_name"] == "Maryam"
    _, mother_headers = signed_in()
    assert client.get("/api/v1/staff/me", headers=mother_headers).status_code == 403
