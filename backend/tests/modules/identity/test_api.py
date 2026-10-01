"""The sign-in flow over HTTP, against PostgreSQL."""
import sqlalchemy as sa

from app.extensions import db
from app.modules.audit.infrastructure.models import AuditLogModel
from app.modules.identity.infrastructure.models import OtpCodeModel, UserModel, UserSessionModel

MOBILE = "0912 123 4567"


def last_code(app):
    return app.extensions["sms_outbox"][-1][1].split()[-1]


def sign_in(app, client, mobile=MOBILE):
    assert client.post("/api/v1/auth/otp/request", json={"mobile": mobile}).status_code == 202
    response = client.post("/api/v1/auth/otp/verify", json={"mobile": mobile, "code": last_code(app)})
    assert response.status_code == 200, response.get_json()
    return response.get_json()


def auth(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_full_sign_in_flow(app, client):
    sent = client.post("/api/v1/auth/otp/request", json={"mobile": MOBILE})
    assert sent.status_code == 202
    assert sent.get_json() == {"mobile": "+989121234567", "expires_in": 120, "resend_after": 60}
    code = last_code(app)
    assert "code" not in sent.get_json() and code not in sent.get_data(as_text=True)

    verified = client.post("/api/v1/auth/otp/verify", json={"mobile": MOBILE, "code": code})
    assert verified.status_code == 200
    tokens = verified.get_json()
    assert tokens["token_type"] == "Bearer" and tokens["expires_in"] == 900
    assert tokens["is_new_user"] is True and tokens["user"]["role"] == "user"

    me = client.get("/api/v1/me", headers=auth(tokens))
    assert me.status_code == 200
    assert me.get_json()["mobile"] == "+989121234567"
    assert me.get_json()["mobile_verified_at"].startswith("20")  # ISO 8601

    refreshed = client.post("/api/v1/auth/token/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    new_tokens = refreshed.get_json()
    assert client.post(
        "/api/v1/auth/token/refresh", json={"refresh_token": tokens["refresh_token"]}
    ).status_code == 401  # rotated

    assert client.post("/api/v1/auth/logout", json={"refresh_token": new_tokens["refresh_token"]}).status_code == 204
    assert client.post(
        "/api/v1/auth/token/refresh", json={"refresh_token": new_tokens["refresh_token"]}
    ).status_code == 401


def test_tokens_from_sign_in_work_on_other_modules(app, client):
    tokens = sign_in(app, client)
    response = client.post(
        "/api/v1/pregnancies",
        json={"lmp_date": "2026-08-01", "conception_type": "natural"},
        headers=auth(tokens),
    )
    assert response.status_code == 201


def test_what_is_stored(app, client):
    sign_in(app, client)
    code = last_code(app)
    otp = db.session.scalar(sa.select(OtpCodeModel))
    assert otp.consumed_at is not None and code not in otp.code_hash
    assert str(otp.request_ip) == "127.0.0.1"
    session = db.session.scalar(sa.select(UserSessionModel))
    assert session.revoked_at is None and len(session.refresh_token_hash) == 64
    events = db.session.scalars(sa.select(AuditLogModel.event_type)).all()
    assert [e.value for e in events] == ["login_succeeded"]


def test_wrong_code_is_counted_even_though_the_request_fails(app, client):
    client.post("/api/v1/auth/otp/request", json={"mobile": MOBILE})
    wrong = "000000" if last_code(app) != "000000" else "111111"
    response = client.post("/api/v1/auth/otp/verify", json={"mobile": MOBILE, "code": wrong})
    assert response.status_code == 422
    assert response.get_json()["error"]["details"] == {"reason": "wrong_code", "attempts_left": 4}
    db.session.remove()
    assert db.session.scalar(sa.select(OtpCodeModel.attempts)) == 1
    assert [e.value for e in db.session.scalars(sa.select(AuditLogModel.event_type))] == ["login_failed"]


def test_resend_too_soon_is_rate_limited(client):
    client.post("/api/v1/auth/otp/request", json={"mobile": MOBILE})
    response = client.post("/api/v1/auth/otp/request", json={"mobile": MOBILE})
    assert response.status_code == 429
    assert response.get_json()["error"]["code"] == "rate_limited"
    assert 0 < int(response.headers["Retry-After"]) <= 60


def test_sms_gateway_failure_returns_503_and_keeps_no_code(app, client, monkeypatch):
    from app import wiring
    from app.modules.identity.application.ports import SmsDeliveryError

    class Down:
        def send_login_code(self, mobile, code):
            raise SmsDeliveryError("down")

    monkeypatch.setattr(wiring, "sms_sender", Down)
    response = client.post("/api/v1/auth/otp/request", json={"mobile": MOBILE})
    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "service_unavailable"
    db.session.remove()
    assert db.session.scalar(sa.select(sa.func.count()).select_from(OtpCodeModel)) == 0


def test_invalid_input(client):
    bad_mobile = client.post("/api/v1/auth/otp/request", json={"mobile": "12345"})
    assert bad_mobile.status_code == 422
    missing = client.post("/api/v1/auth/otp/request", json={})
    assert missing.status_code == 422
    assert missing.get_json()["error"]["details"]["fields"][0]["field"] == "mobile"


def test_deactivated_user_is_signed_out_everywhere(app, client):
    tokens = sign_in(app, client)
    user = db.session.scalar(sa.select(UserModel))
    user.is_active = False
    db.session.commit()
    assert client.get("/api/v1/me", headers=auth(tokens)).status_code == 401
    assert client.post(
        "/api/v1/auth/token/refresh", json={"refresh_token": tokens["refresh_token"]}
    ).status_code == 401
