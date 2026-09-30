import uuid

import sqlalchemy as sa

from app.extensions import db

from .models import UserModel


def is_user_active(user_id: uuid.UUID) -> bool:
    """True when the user exists and has not been deactivated."""
    return bool(db.session.scalar(sa.select(UserModel.is_active).where(UserModel.id == user_id)))
