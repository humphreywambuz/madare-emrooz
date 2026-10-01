"""Care team endpoints.

Admins:   create and manage staff accounts; see alerts from mothers with no midwife.
Mothers:  list the midwives and choose one.
Staff:    patient list, red alert inbox.
"""
from dataclasses import asdict

from flask import Blueprint, jsonify

from app.modules.identity.domain.enums import UserRole
from app.shared.api.auth import roles_required
from app.shared.api.http import current_actor, parse_body
from app.wiring import care_team_service, staff_service

from .schemas import ChooseMidwifeBody, CreateStaffBody, UpdateStaffBody

bp = Blueprint("care_team", __name__, url_prefix="/api/v1")

ADMIN = UserRole.ADMIN
MOTHER = UserRole.USER
CLINICIANS = (UserRole.DOCTOR, UserRole.MIDWIFE)


def _list(items):
    return jsonify(items=[asdict(i) for i in items])


# --- admins ------------------------------------------------------------------------


@bp.post("/admin/staff")
@roles_required(ADMIN)
def create_staff():
    body = parse_body(CreateStaffBody)
    return jsonify(asdict(staff_service().create_staff(current_actor(), **body.model_dump()))), 201


@bp.get("/admin/staff")
@roles_required(ADMIN)
def list_staff():
    return _list(staff_service().list_staff())


@bp.patch("/admin/staff/<uuid:user_id>")
@roles_required(ADMIN)
def update_staff(user_id):
    changes = parse_body(UpdateStaffBody).model_dump(exclude_unset=True)
    return jsonify(asdict(staff_service().update_staff(current_actor(), user_id, changes)))


@bp.get("/admin/unassigned-alerts")
@roles_required(ADMIN)
def unassigned_alerts():
    """Red alerts from mothers who haven't chosen a midwife yet."""
    return _list(care_team_service().alert_inbox(current_actor()))


# --- mothers -----------------------------------------------------------------------


@bp.get("/midwives")
@roles_required(MOTHER)
def list_midwives():
    return _list(staff_service().list_midwives())


@bp.get("/my-midwife")
@roles_required(MOTHER)
def my_midwife():
    midwife = staff_service().my_midwife(current_actor().user_id)
    return jsonify(midwife=asdict(midwife) if midwife else None)


@bp.put("/my-midwife")
@roles_required(MOTHER)
def choose_midwife():
    body = parse_body(ChooseMidwifeBody)
    return jsonify(midwife=asdict(staff_service().choose_midwife(current_actor(), body.midwife_id)))


# --- staff -------------------------------------------------------------------------


@bp.get("/staff/patients")
@roles_required(*CLINICIANS)
def list_patients():
    return _list(care_team_service().list_patients(current_actor()))


@bp.get("/staff/alerts")
@roles_required(UserRole.MIDWIFE)
def midwife_alerts():
    return _list(care_team_service().alert_inbox(current_actor()))


@bp.post("/staff/alerts/<uuid:alert_id>/seen")
@roles_required(UserRole.MIDWIFE, ADMIN)
def mark_alert_seen(alert_id):
    care_team_service().mark_alert_seen(current_actor(), alert_id)
    return "", 204
