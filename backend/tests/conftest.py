import pytest
from sqlalchemy.orm import Session

from app import create_app
from app.config import TestConfig
from app.extensions import db as _db


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
