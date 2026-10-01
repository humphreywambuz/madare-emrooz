"""Care team endpoints.

Admins:   create and manage staff accounts; see alerts from mothers with no midwife.
Mothers:  list the midwives and choose one.
Staff:    patient list, red alert inbox, summary card, full record, notes, tags, approvals.
"""
from dataclasses import asdict

from flask import Blueprint, jsonify, request

from app.modules.identity.domain.enums import UserRole
from app.shared.api.auth import roles_required
from app.shared.api.http import current_actor, parse_body
from app.shared.domain.errors import NotFoundError
from app.modules.care_team.domain.enums import ApprovalScope, RiskTag
from app.wiring import care_team_service, clinical_service, staff_service

from .record import full_record, summary_card
from .schemas import (
    ApprovalBody,
    ChooseMidwifeBody,
    CreateStaffBody,
    NoteBody,
    PatientListQuery,
    RiskTagBody,
    UpdateStaffBody,
)

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


@bp.get("/staff/me")
@roles_required(UserRole.DOCTOR, UserRole.MIDWIFE, ADMIN)
def staff_me():
    """The signed-in staff member's name and role, for the panel's header."""
    return jsonify(asdict(staff_service().get_staff(current_actor().user_id)))


@bp.get("/staff/patients")
@roles_required(*CLINICIANS)
def list_patients():
    """?q= searches name, mobile or national code; ?page=1&per_page=20 (max 100)."""
    query = PatientListQuery.model_validate(request.args.to_dict())
    page = care_team_service().list_patients(
        current_actor(), query=query.q, page=query.page, per_page=query.per_page
    )
    return jsonify(asdict(page))


@bp.get("/staff/alerts")
@roles_required(UserRole.MIDWIFE)
def midwife_alerts():
    return _list(care_team_service().alert_inbox(current_actor()))


@bp.post("/staff/alerts/<uuid:alert_id>/seen")
@roles_required(UserRole.MIDWIFE, ADMIN)
def mark_alert_seen(alert_id):
    care_team_service().mark_alert_seen(current_actor(), alert_id)
    return "", 204


# --- one mother's record -------------------------------------------------------------


@bp.get("/staff/patients/<uuid:patient_id>/summary")
@roles_required(*CLINICIANS)
def patient_summary(patient_id):
    return jsonify(summary_card(current_actor(), patient_id))


@bp.get("/staff/patients/<uuid:patient_id>/record")
@roles_required(*CLINICIANS)
def patient_record(patient_id):
    return jsonify(full_record(current_actor(), patient_id))


@bp.post("/staff/patients/<uuid:patient_id>/notes")
@roles_required(*CLINICIANS)
def add_note(patient_id):
    clinical_service().add_note(current_actor(), patient_id, parse_body(NoteBody).body)
    return "", 201


@bp.post("/staff/patients/<uuid:patient_id>/risk-tags")
@roles_required(*CLINICIANS)
def add_risk_tag(patient_id):
    body = parse_body(RiskTagBody)
    clinical_service().add_risk_tag(current_actor(), patient_id, body.tag, body.note)
    return "", 201


@bp.delete("/staff/patients/<uuid:patient_id>/risk-tags/<tag>")
@roles_required(*CLINICIANS)
def remove_risk_tag(patient_id, tag):
    clinical_service().remove_risk_tag(current_actor(), patient_id, _enum(RiskTag, tag))
    return "", 204


@bp.post("/staff/patients/<uuid:patient_id>/approvals")
@roles_required(UserRole.DOCTOR)
def approve(patient_id):
    clinical_service().approve(current_actor(), patient_id, parse_body(ApprovalBody).scope)
    return "", 201


@bp.delete("/staff/patients/<uuid:patient_id>/approvals/<scope>")
@roles_required(UserRole.DOCTOR)
def revoke_approval(patient_id, scope):
    clinical_service().revoke(current_actor(), patient_id, _enum(ApprovalScope, scope))
    return "", 204


def _enum(enum_cls, value):
    try:
        return enum_cls(value)
    except ValueError:
        raise NotFoundError(f"Unknown {enum_cls.__name__}: {value}.") from None
