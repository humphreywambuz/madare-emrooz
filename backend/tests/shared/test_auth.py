import uuid

from app.extensions import db
from app.modules.identity.infrastructure.models import UserModel
from app.shared.infrastructure.tokens import AccessTokenService

URL = "/api/v1/pregnancies/current"


def test_deactivated_account_is_rejected(client, signed_in):
    user_id, headers = signed_in()
    db.session.get(UserModel, user_id).is_active = False
    db.session.commit()

    response = client.get(URL, headers=headers)
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "unauthenticated"


def test_token_for_unknown_user_is_rejected(app, client):
    token = AccessTokenService(app.config["SECRET_KEY"], 60).issue(uuid.uuid4(), "user")
    response = client.get(URL, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_unknown_api_urls_answer_in_json(client):
    missing = client.get("/api/v1/nothing-here")
    assert missing.status_code == 404 and missing.get_json()["error"]["code"] == "not_found"
    wrong_method = client.delete("/api/v1/auth/otp/request")
    assert wrong_method.status_code == 405 and wrong_method.get_json()["error"]["code"] == "method_not_allowed"
