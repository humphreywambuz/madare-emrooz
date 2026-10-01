"""Daily logs. The mother reports only spotting or bleeding; her midwife records the rest."""
from dataclasses import asdict

from flask import Blueprint, jsonify

from app.modules.identity.domain.enums import UserRole
from app.shared.api.auth import roles_required
from app.shared.api.http import current_actor, parse_body
from app.wiring import monitoring_service as _service

from .schemas import BleedingReportBody, MidwifeLogBody

bp = Blueprint("monitoring", __name__, url_prefix="/api/v1")


def _view(log) -> dict:
    return {**asdict(log), "is_red_alert": log.is_red_alert}


@bp.post("/daily-logs")
@roles_required(UserRole.USER)
def report_bleeding():
    body = parse_body(BleedingReportBody)
    return jsonify(_view(_service().report_bleeding(current_actor(), body.has_spotting_or_bleeding))), 201


@bp.get("/daily-logs")
@roles_required(UserRole.USER)
def own_logs():
    return jsonify(items=[_view(log) for log in _service().own_logs(current_actor().user_id)])


@bp.post("/staff/patients/<uuid:patient_id>/daily-logs")
@roles_required(UserRole.MIDWIFE)
def record_for_patient(patient_id):
    values = parse_body(MidwifeLogBody).model_dump(exclude_none=True)
    return jsonify(_view(_service().record_for_patient(current_actor(), patient_id, values))), 201


@bp.get("/staff/patients/<uuid:patient_id>/daily-logs")
@roles_required(UserRole.MIDWIFE, UserRole.DOCTOR)
def logs_for_patient(patient_id):
    logs = _service().logs_for_patient(current_actor(), patient_id)
    return jsonify(items=[_view(log) for log in logs])
