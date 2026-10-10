"""HTTP adapter for the pregnancy module: parse the request, call a use case,
serialise the result. No business rules live here.

Partner Mode: the mother makes a QR code (POST /partner-link). Her spouse scans it and
opens /p/<token>, a page with the pregnancy week and due date; he doesn't sign in.
"""
import base64
import hashlib
from dataclasses import asdict
from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template_string, request

from app.modules.identity.domain.enums import UserRole
from app.modules.pregnancy.application.services import StartPregnancy
from app.shared.api.auth import current_user, login_required, roles_required
from app.shared.api.http import current_actor, parse_body, request_context
from app.shared.domain.errors import NotFoundError, ValidationError
from app.shared.domain.jalali import format_jalali, persian_digits
from app.wiring import partner_service, pregnancy_service as _service

from .schemas import (
    CorrectDueDateRequest,
    CorrectPregnancyRequest,
    EndPregnancyRequest,
    StartPregnancyRequest,
)

bp = Blueprint("pregnancy", __name__)

_PARTNER_PAGE = (Path(__file__).with_name("partner_page.html")).read_text(encoding="utf-8")


def _style_hash(page: str) -> str:
    """CSP hash of the page's one <style> block, so it applies and nothing else can."""
    style = page.split("<style>", 1)[1].split("</style>", 1)[0]
    return "'sha256-" + base64.b64encode(hashlib.sha256(style.encode()).digest()).decode() + "'"


# The page has no scripts, images or fonts of its own: only its stylesheet may apply.
_PARTNER_PAGE_POLICY = (
    f"default-src 'none'; style-src {_style_hash(_PARTNER_PAGE)}; "
    "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)


@bp.post("/api/v1/pregnancies")
@login_required
def start_pregnancy():
    body = StartPregnancyRequest.model_validate(request.get_json(silent=True) or {})
    view = _service().start(StartPregnancy(user_id=current_user().user_id, **body.model_dump()))
    return jsonify(asdict(view)), 201


@bp.get("/api/v1/pregnancies/current")
@login_required
def get_current_pregnancy():
    return jsonify(asdict(_service().get_active(current_user().user_id)))


@bp.patch("/api/v1/pregnancies/current")
@roles_required(UserRole.USER)
def correct_current_pregnancy():
    """Fix a wrong LMP, cycle length, conception type or care provider."""
    changes = parse_body(CorrectPregnancyRequest).model_dump(exclude_unset=True)
    nulls = sorted(k for k, v in changes.items() if v is None and k not in ("care_provider_type", "care_provider_name"))
    if nulls:
        raise ValidationError("These fields can't be empty.", details={"fields": nulls})
    return jsonify(asdict(_service().correct(current_actor(), changes)))


@bp.put("/api/v1/staff/patients/<uuid:patient_id>/pregnancy/due-date")
@roles_required(UserRole.MIDWIFE, UserRole.DOCTOR)
def correct_due_date(patient_id):
    """Her care team sets the due date, e.g. from an ultrasound."""
    body = parse_body(CorrectDueDateRequest)
    view = _service().correct_due_date(current_actor(), patient_id, body.estimated_due_date, body.reason)
    return jsonify(asdict(view))


@bp.post("/api/v1/pregnancies/current/end")
@login_required
def end_current_pregnancy():
    body = parse_body(EndPregnancyRequest)
    return jsonify(asdict(_service().end_active(current_user().user_id, body.status)))


# --- Partner Mode ------------------------------------------------------------------


def _link_json(link):
    base = current_app.config["PUBLIC_BASE_URL"] or request.host_url
    return {"url": f"{base.rstrip('/')}/p/{link.token}", "token": link.token, "created_at": link.created_at}


@bp.post("/api/v1/partner-link")
@roles_required(UserRole.USER)
def create_partner_link():
    return jsonify(_link_json(partner_service().create_link(current_actor()))), 201


@bp.get("/api/v1/partner-link")
@roles_required(UserRole.USER)
def get_partner_link():
    return jsonify(_link_json(partner_service().current_link(current_actor().user_id)))


@bp.delete("/api/v1/partner-link")
@roles_required(UserRole.USER)
def revoke_partner_link():
    partner_service().revoke_link(current_actor())
    return "", 204


@bp.get("/api/v1/partner/<token>")
def partner_view(token):
    """JSON for a partner app or widget; no sign-in."""
    return _no_store(jsonify(asdict(partner_service().view(token, request_context()))))


@bp.get("/p/<token>")
def partner_page(token):
    """The page the QR code opens on the spouse's phone."""
    try:
        view = partner_service().view(token, request_context())
    except NotFoundError:
        return _partner_page(render_template_string(_PARTNER_PAGE, view=None), 404)
    html = render_template_string(
        _PARTNER_PAGE,
        view=view,
        week=persian_digits(view.gestational_week),
        days=persian_digits(view.gestational_days) if view.gestational_days else None,
        due_date=format_jalali(view.estimated_due_date),
        days_left=persian_digits(view.days_until_due),
    )
    return _partner_page(html)


def _no_store(response):
    response = current_app.make_response(response)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


def _partner_page(html: str, status: int = 200):
    response = _no_store(current_app.make_response((html, status)))
    response.headers["Content-Security-Policy"] = _PARTNER_PAGE_POLICY
    return response
