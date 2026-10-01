"""Sign-in endpoints. Flow for the app:

1. POST /auth/otp/request  {mobile}          -> code sent by SMS
2. POST /auth/otp/verify   {mobile, code}    -> access + refresh tokens
3. POST /auth/token/refresh {refresh_token}  -> new tokens (old refresh token stops working)
4. POST /auth/logout       {refresh_token}   -> session ended
"""
from flask import Blueprint, jsonify

from app.modules.identity.application.services import SignedIn
from app.shared.api.auth import current_user, login_required
from app.shared.api.http import parse_body, request_context
from app.wiring import auth_service

from .schemas import OtpRequestBody, OtpVerifyBody, RefreshTokenBody

bp = Blueprint("identity", __name__, url_prefix="/api/v1")


def _tokens(result: SignedIn) -> dict:
    return {
        "token_type": "Bearer",
        "access_token": result.access_token,
        "expires_in": result.access_token_expires_in,
        "refresh_token": result.refresh_token,
        "refresh_token_expires_at": result.refresh_token_expires_at,
        "user": {"id": result.user_id, "role": result.role},
        "is_new_user": result.is_new_user,
    }


@bp.post("/auth/otp/request")
def request_otp():
    body = parse_body(OtpRequestBody)
    sent = auth_service().request_otp(body.mobile, request_context())
    return jsonify(
        mobile=sent.mobile,
        expires_in=sent.expires_in_seconds,
        resend_after=sent.resend_after_seconds,
    ), 202


@bp.post("/auth/otp/verify")
def verify_otp():
    body = parse_body(OtpVerifyBody)
    return jsonify(_tokens(auth_service().verify_otp(body.mobile, body.code, request_context())))


@bp.post("/auth/token/refresh")
def refresh_token():
    body = parse_body(RefreshTokenBody)
    return jsonify(_tokens(auth_service().refresh(body.refresh_token, request_context())))


@bp.post("/auth/logout")
def logout():
    auth_service().logout(parse_body(RefreshTokenBody).refresh_token)
    return "", 204


@bp.get("/me")
@login_required
def me():
    user = auth_service().get_user(current_user().user_id)
    return jsonify(
        id=user.id,
        mobile=user.mobile,
        role=user.role,
        mobile_verified_at=user.mobile_verified_at,
        last_login_at=user.last_login_at,
    )
