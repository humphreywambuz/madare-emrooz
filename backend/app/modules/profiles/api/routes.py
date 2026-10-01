"""Onboarding: the mother's profile and medical history.

After sign-in the app calls GET /profile. 404 means a new user, so it starts onboarding;
otherwise ``home`` says which home screen to open.
"""
from dataclasses import asdict

from flask import Blueprint, jsonify

from app.shared.api.auth import current_user, login_required
from app.shared.api.http import current_actor, parse_body
from app.wiring import profile_service as _service

from .schemas import MedicalHistoryBody, ProfileBody

bp = Blueprint("profiles", __name__, url_prefix="/api/v1")


@bp.get("/profile")
@login_required
def get_profile():
    return jsonify(asdict(_service().get_profile(current_user().user_id)))


@bp.put("/profile")
@login_required
def save_profile():
    body = parse_body(ProfileBody)
    view, created = _service().save_profile(current_actor(), body.model_dump())
    return jsonify(asdict(view)), 201 if created else 200


@bp.get("/medical-history")
@login_required
def get_medical_history():
    return jsonify(asdict(_service().get_medical_history(current_user().user_id)))


@bp.put("/medical-history")
@login_required
def save_medical_history():
    body = parse_body(MedicalHistoryBody)
    history, created = _service().save_medical_history(current_actor(), body.model_dump())
    return jsonify(asdict(history)), 201 if created else 200
