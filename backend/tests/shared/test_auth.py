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
