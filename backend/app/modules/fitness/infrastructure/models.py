"""Section 9: fitness & daily sport path (option B)."""
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.modules.fitness.domain.enums import FitnessGoal
from app.shared.infrastructure.orm import TimestampMixin, enum_column


class FitnessProfileModel(TimestampMixin, db.Model):
    """Identity fields (name, mobile, age, height, weight) live in users/profiles."""

    __tablename__ = "fitness_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    goal: Mapped[FitnessGoal] = mapped_column(enum_column(FitnessGoal))
    goal_note: Mapped[str | None] = mapped_column(sa.Text)
