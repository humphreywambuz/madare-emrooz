"""Section 8: security audit log."""
import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import enum_column
from .enums import AuditEventType


class AuditLog(db.Model):
    """Append-only record of every access or change to health data.

    ``actor_id`` and ``patient_id`` deliberately have no foreign keys: audit
    rows must outlive the rows they describe and must never block a delete.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        sa.Index("ix_audit_logs_actor_created_at", "actor_id", "created_at"),
        sa.Index("ix_audit_logs_patient_created_at", "patient_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(sa.BigInteger, sa.Identity(), primary_key=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    patient_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    event_type: Mapped[AuditEventType] = mapped_column(enum_column(AuditEventType), index=True)
    resource_type: Mapped[str | None] = mapped_column(sa.String(50))  # e.g. "medical_documents"
    resource_id: Mapped[str | None] = mapped_column(sa.String(64))
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(sa.Text)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), index=True
    )
