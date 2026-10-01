"""Uploading and viewing medical documents over HTTP."""
import io

import sqlalchemy as sa

from app.extensions import db
from app.modules.audit.infrastructure.models import AuditLogModel
from app.modules.identity.domain.enums import UserRole
from tests.modules.monitoring.test_api import listed_midwife, pregnant_mother

PDF = b"%PDF-1.7\n" + b"x" * 100
PNG = b"\x89PNG\r\n\x1a\n" + b"x" * 100


def upload(client, headers, patient_id, content=PDF, name="آزمایش خون.pdf", **fields):
    data = {"document_type": "blood_test", **fields}
    if content is not None:
        data["file"] = (io.BytesIO(content), name)
    return client.post(
        f"/api/v1/staff/patients/{patient_id}/documents",
        data=data,
        headers=headers,
        content_type="multipart/form-data",
    )


def test_midwife_uploads_and_everyone_allowed_can_view(client, signed_in):
    midwife_id, midwife = listed_midwife(client, signed_in)
    _, doctor = signed_in(UserRole.DOCTOR)
    mother_id, mother = pregnant_mother(client, signed_in, midwife_id)

    response = upload(
        client, midwife, mother_id, performed_at="2026-09-20T09:30:00+03:30",
        fundal_height_cm="24.5", fetal_heart_rate_bpm="140", notes="",
    )
    assert response.status_code == 201, response.get_json()
    document = response.get_json()
    assert document["content_type"] == "application/pdf"
    assert document["original_filename"] == "آزمایش خون.pdf"
    assert document["file_size_bytes"] == len(PDF)
    assert document["pregnancy_id"] is not None and document["fundal_height_cm"] == 24.5
    assert "storage_key" not in document

    listed = client.get(f"/api/v1/staff/patients/{mother_id}/documents", headers=doctor).get_json()["items"]
    assert [d["id"] for d in listed] == [document["id"]]

    staff_file = client.get(f"/api/v1/staff/patients/{mother_id}/documents/{document['id']}/file", headers=doctor)
    assert staff_file.status_code == 200 and staff_file.data == PDF
    assert staff_file.headers["Content-Type"] == "application/pdf"
    assert staff_file.headers["X-Content-Type-Options"] == "nosniff"

    # The mother sees her own documents.
    assert len(client.get("/api/v1/documents", headers=mother).get_json()["items"]) == 1
    assert client.get(f"/api/v1/documents/{document['id']}/file", headers=mother).data == PDF

    events = [e.value for e in db.session.scalars(sa.select(AuditLogModel.event_type))]
    assert "document_uploaded" in events and events.count("record_viewed") == 2


def test_only_her_midwife_uploads(client, signed_in):
    midwife_id, _ = listed_midwife(client, signed_in)
    _, other_midwife = listed_midwife(client, signed_in)
    _, doctor = signed_in(UserRole.DOCTOR)
    mother_id, mother = pregnant_mother(client, signed_in, midwife_id)
    assert upload(client, other_midwife, mother_id).status_code == 403
    assert upload(client, doctor, mother_id).status_code == 403
    assert upload(client, mother, mother_id).status_code == 403


def test_file_checks(app, client, signed_in):
    midwife_id, midwife = listed_midwife(client, signed_in)
    mother_id, _ = pregnant_mother(client, signed_in, midwife_id)
    assert upload(client, midwife, mother_id, content=PNG, name="scan.png").get_json()["content_type"] == "image/png"
    # The type is read from the file itself, not from its name.
    assert upload(client, midwife, mother_id, content=b"<html>", name="x.pdf").status_code == 422
    assert upload(client, midwife, mother_id, content=None).status_code == 422
    assert upload(client, midwife, mother_id, document_type="selfie").status_code == 422
    assert upload(client, midwife, mother_id, fetal_heart_rate_bpm="400").status_code == 422

    app.config["DOCUMENT_MAX_BYTES"] = 50
    try:
        assert upload(client, midwife, mother_id).status_code == 422
    finally:
        app.config["DOCUMENT_MAX_BYTES"] = 10 * 1024 * 1024


def test_request_over_the_limit_is_refused(app, client, signed_in):
    midwife_id, midwife = listed_midwife(client, signed_in)
    mother_id, _ = pregnant_mother(client, signed_in, midwife_id)
    big = b"%PDF-" + b"x" * (app.config["MAX_CONTENT_LENGTH"] + 1)
    response = upload(client, midwife, mother_id, content=big)
    assert response.status_code == 413 and response.get_json()["error"]["code"] == "too_large"


def test_mother_cannot_open_someone_elses_document(client, signed_in):
    midwife_id, midwife = listed_midwife(client, signed_in)
    mother_id, _ = pregnant_mother(client, signed_in, midwife_id)
    _, stranger = signed_in()
    document = upload(client, midwife, mother_id).get_json()
    assert client.get(f"/api/v1/documents/{document['id']}/file", headers=stranger).status_code == 404
