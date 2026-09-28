import pytest
from sqlalchemy.exc import IntegrityError, StatementError

from app.modules.identity.domain.enums import UserRole
from app.modules.identity.infrastructure.models import UserModel


def test_user_defaults(session, make_user):
    user = make_user()
    session.refresh(user)
    assert user.role is UserRole.USER
    assert user.is_active is True
    assert user.is_staff is False
    assert user.created_at is not None


def test_mobile_must_be_e164(session):
    session.add(UserModel(mobile="09121234567"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_invalid_enum_value_is_rejected(session):
    session.add(UserModel(mobile="+989121234567", role="superuser"))
    with pytest.raises(StatementError):
        session.flush()
