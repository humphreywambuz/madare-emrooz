import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app import create_app
from app.config import TestConfig
from app.extensions import db as _db
from app.modules.identity.domain.enums import UserRole
from app.modules.identity.infrastructure.models import UserModel
from app.shared.infrastructure.tokens import AccessTokenService


@pytest.fixture(scope="session")
def app():
    app = create_app(TestConfig)
    with app.app_context():
        _db.drop_all()
        _db.create_all()
        yield app
        _db.drop_all()
        _db.engine.dispose()


@pytest.fixture()
def session(app):
    """A session whose work is rolled back after each test."""
    connection = _db.engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def make_user(session):
    counter = iter(range(1000, 10000))

    def _make(role: UserRole = UserRole.USER) -> UserModel:
        user = UserModel(mobile=f"+98912000{next(counter)}", role=role)
        session.add(user)
        session.flush()
        return user

    return _make


@pytest.fixture()
def client(app):
    """HTTP client for API tests. Requests commit, so tables are emptied afterwards."""
    app.extensions.setdefault("sms_outbox", []).clear()
    yield app.test_client()
    _db.session.remove()
    tables = ", ".join(t.name for t in _db.metadata.sorted_tables)
    with _db.engine.begin() as conn:
        conn.execute(sa.text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture()
def signed_in(app, client):
    """Create a committed user and return (user_id, auth headers)."""

    def _signed_in(role: UserRole = UserRole.USER):
        user = UserModel(mobile=f"+98935{uuid.uuid4().int % 10**7:07d}", role=role)
        _db.session.add(user)
        _db.session.commit()
        token = AccessTokenService(app.config["SECRET_KEY"], 60).issue(user.id, role.value)
        return user.id, {"Authorization": f"Bearer {token}"}

    return _signed_in
