"""ORM building blocks shared by every module's infrastructure layer."""
import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


def enum_column(enum_cls: type[enum.Enum]) -> sa.Enum:
    """Store an enum as VARCHAR + CHECK constraint.

    Native PostgreSQL ENUM types are awkward to alter in migrations, so enum
    values are persisted as their string value. The CHECK constraint is added
    per column by ``_add_enum_check_constraint`` below.
    """
    type_ = sa.Enum(
        enum_cls,
        native_enum=False,
        create_constraint=False,
        length=40,
        validate_strings=True,
        values_callable=lambda members: [m.value for m in members],
    )
    type_._needs_check_constraint = True
    return type_


@sa.event.listens_for(sa.Column, "after_parent_attach")
def _add_enum_check_constraint(column: sa.Column, parent) -> None:
    # SQLAlchemy's own Enum constraint is named after the enum type, which
    # collides when one enum is used by two columns of the same table (and
    # Alembic renders it twice), so emit one explicitly named CHECK per column.
    if not isinstance(parent, sa.Table):
        return
    # Only model columns built by enum_column(); Alembic migrations already
    # spell out their CHECK constraints.
    if getattr(column.type, "_needs_check_constraint", False):
        parent.append_constraint(
            sa.CheckConstraint(column.in_(column.type.enums), name=f"{column.name}_valid")
        )


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
    )


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )
