"""Section 6: medical documents storage."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import TimestampMixin, UUIDPrimaryKeyMixin, enum_column
from .enums import DocumentType

if TYPE_CHECKING:
    from .user import User


class MedicalDocument(UUIDPrimaryKeyMixin, TimestampMixin, db.Model):
    """An uploaded test result or image (photo or PDF).

    The file itself lives in object/file storage; only its key is stored here.
    """

    __tablename__ = "medical_documents"
    __table_args__ = (
        sa.CheckConstraint("file_size_bytes > 0", name="file_size_positive"),
        sa.CheckConstraint("fundal_height_cm BETWEEN 5 AND 60", name="fundal_height_range"),
        sa.CheckConstraint("fetal_heart_rate_bpm BETWEEN 50 AND 250", name="fetal_hr_range"),
        sa.Index("ix_medical_documents_patient_performed_at", "patient_id", "performed_at"),
    )

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")
    )
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.id")
    )
    pregnancy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("pregnancies.id", ondelete="SET NULL")
    )
    document_type: Mapped[DocumentType] = mapped_column(enum_column(DocumentType))

    storage_key: Mapped[str] = mapped_column(sa.String(512), unique=True)
    original_filename: Mapped[str] = mapped_column(sa.String(255))
    content_type: Mapped[str] = mapped_column(sa.String(100))  # image/jpeg, application/pdf
    file_size_bytes: Mapped[int] = mapped_column(sa.BigInteger)

    performed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    fundal_height_cm: Mapped[Decimal | None] = mapped_column(sa.Numeric(4, 1))
    fetal_heart_rate_bpm: Mapped[int | None] = mapped_column(sa.SmallInteger)
    notes: Mapped[str | None] = mapped_column(sa.Text)

    patient: Mapped["User"] = relationship(foreign_keys=[patient_id])
    uploaded_by: Mapped["User"] = relationship(foreign_keys=[uploaded_by_id])
