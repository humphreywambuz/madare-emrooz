from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.documents.domain.enums import DocumentType


class UploadForm(BaseModel):
    """Form fields sent with the file (multipart/form-data)."""

    model_config = ConfigDict(extra="forbid")

    document_type: DocumentType
    performed_at: datetime | None = None
    fundal_height_cm: Decimal | None = Field(default=None, ge=5, le=60, decimal_places=1)
    fetal_heart_rate_bpm: int | None = Field(default=None, ge=50, le=250)
    notes: str | None = Field(default=None, max_length=2000)


class RemoveDocumentBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, max_length=500)  # e.g. "uploaded to the wrong mother"
