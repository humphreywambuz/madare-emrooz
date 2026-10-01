"""Medical documents (spec section 6). Pure Python: no Flask, no SQLAlchemy."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from .enums import DocumentType

# Accepted files, recognised by their first bytes rather than the name or the browser's
# claim, so a renamed executable or HTML page is refused.
_SIGNATURES = {
    "image/jpeg": b"\xff\xd8\xff",
    "image/png": b"\x89PNG\r\n\x1a\n",
    "application/pdf": b"%PDF-",
}
ALLOWED_CONTENT_TYPES = tuple(_SIGNATURES)


def detect_content_type(content: bytes) -> str | None:
    return next((t for t, magic in _SIGNATURES.items() if content.startswith(magic)), None)


def clean_filename(name: str | None) -> str:
    """Keep only the file's own name (no folders), at most 255 characters."""
    base = (name or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
    return base[-255:] or "document"


@dataclass
class MedicalDocument:
    patient_id: uuid.UUID
    uploaded_by_id: uuid.UUID
    document_type: DocumentType
    original_filename: str
    content_type: str
    file_size_bytes: int
    created_at: datetime
    pregnancy_id: uuid.UUID | None = None
    performed_at: datetime | None = None
    fundal_height_cm: Decimal | None = None
    fetal_heart_rate_bpm: int | None = None
    notes: str | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Files are kept in PostgreSQL (document_files); the key records where.
    storage_key: str = ""

    def __post_init__(self):
        if not self.storage_key:
            self.storage_key = f"db:{self.id}"
