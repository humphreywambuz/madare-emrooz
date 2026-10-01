"""Medical documents. The midwife uploads (multipart/form-data with a ``file`` field);
the mother and her care team can view them."""
import io
from dataclasses import asdict

from flask import Blueprint, jsonify, request, send_file

from app.modules.identity.domain.enums import UserRole
from app.shared.api.auth import roles_required
from app.shared.api.http import current_actor
from app.wiring import document_service as _service

from .schemas import UploadForm

bp = Blueprint("documents", __name__, url_prefix="/api/v1")


def _view(document) -> dict:
    view = asdict(document)
    view.pop("storage_key")
    return view


def _file_response(document, content: bytes):
    response = send_file(
        io.BytesIO(content),
        mimetype=document.content_type,
        download_name=document.original_filename,
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "private, no-store"
    return response


@bp.post("/staff/patients/<uuid:patient_id>/documents")
@roles_required(UserRole.MIDWIFE)
def upload(patient_id):
    fields = {k: v for k, v in request.form.items() if v != ""}
    form = UploadForm.model_validate(fields)
    upload = request.files.get("file")
    document = _service().upload(
        current_actor(),
        patient_id,
        filename=upload.filename if upload else None,
        content=upload.read() if upload else b"",
        **form.model_dump(),
    )
    return jsonify(_view(document)), 201


@bp.get("/staff/patients/<uuid:patient_id>/documents")
@roles_required(UserRole.MIDWIFE, UserRole.DOCTOR)
def documents_for_patient(patient_id):
    documents = _service().documents_for_patient(current_actor(), patient_id)
    return jsonify(items=[_view(d) for d in documents])


@bp.get("/staff/patients/<uuid:patient_id>/documents/<uuid:document_id>/file")
@roles_required(UserRole.MIDWIFE, UserRole.DOCTOR)
def file_for_patient(patient_id, document_id):
    return _file_response(*_service().file_for_patient(current_actor(), patient_id, document_id))


@bp.get("/documents")
@roles_required(UserRole.USER)
def own_documents():
    return jsonify(items=[_view(d) for d in _service().own_documents(current_actor().user_id)])


@bp.get("/documents/<uuid:document_id>/file")
@roles_required(UserRole.USER)
def own_file(document_id):
    return _file_response(*_service().own_file(current_actor().user_id, document_id))
