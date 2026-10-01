"""Rehabilitation path: the questionnaire, the specialist visit and the imaging link."""
from dataclasses import asdict

from flask import Blueprint, jsonify

from app.modules.identity.domain.enums import UserRole
from app.shared.api.auth import roles_required
from app.shared.api.http import current_actor, parse_body
from app.wiring import rehab_service as _service

from .schemas import ImagingBody, RehabBody

bp = Blueprint("rehabilitation", __name__, url_prefix="/api/v1")


def _json(view):
    return {**asdict(view.profile), "is_advanced_locked": view.is_advanced_locked}


@bp.get("/rehab-profile")
@roles_required(UserRole.USER)
def get_own():
    return jsonify(_json(_service().get_own(current_actor().user_id)))


@bp.put("/rehab-profile")
@roles_required(UserRole.USER)
def save_own():
    answers = parse_body(RehabBody).model_dump(exclude_none=True)
    view, created = _service().save_own(current_actor(), answers)
    return jsonify(_json(view)), 201 if created else 200


@bp.post("/staff/patients/<uuid:patient_id>/rehab-profile/specialist-visit")
@roles_required(UserRole.DOCTOR, UserRole.MIDWIFE)
def record_specialist_visit(patient_id):
    return jsonify(_json(_service().record_specialist_visit(current_actor(), patient_id)))


@bp.put("/staff/patients/<uuid:patient_id>/rehab-profile/imaging")
@roles_required(UserRole.MIDWIFE)
def attach_imaging(patient_id):
    body = parse_body(ImagingBody)
    return jsonify(_json(_service().attach_imaging(current_actor(), patient_id, body.document_id)))
