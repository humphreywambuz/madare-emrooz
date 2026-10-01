"""Fitness path: her goal, and the dashboard that opens after the specialist visit."""
from dataclasses import asdict

from flask import Blueprint, jsonify

from app.modules.identity.domain.enums import UserRole
from app.shared.api.auth import roles_required
from app.shared.api.http import current_actor, parse_body
from app.wiring import fitness_service as _service

from .schemas import FitnessBody

bp = Blueprint("fitness", __name__, url_prefix="/api/v1")


@bp.get("/fitness-profile")
@roles_required(UserRole.USER)
def get_own():
    return jsonify(asdict(_service().get_own(current_actor().user_id)))


@bp.put("/fitness-profile")
@roles_required(UserRole.USER)
def save_own():
    body = parse_body(FitnessBody)
    view, created = _service().save_own(current_actor(), body.goal, body.goal_note)
    return jsonify(asdict(view)), 201 if created else 200


@bp.post("/staff/patients/<uuid:patient_id>/fitness-profile/specialist-visit")
@roles_required(UserRole.DOCTOR, UserRole.MIDWIFE)
def record_specialist_visit(patient_id):
    return jsonify(asdict(_service().record_specialist_visit(current_actor(), patient_id)))
