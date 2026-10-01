import uuid
from typing import Protocol

from app.modules.documents.domain.entities import MedicalDocument


class DocumentRepository(Protocol):
    def add(self, document: MedicalDocument, content: bytes) -> None: ...

    def get(self, document_id: uuid.UUID) -> MedicalDocument | None: ...

    def content(self, document_id: uuid.UUID) -> bytes: ...

    def delete(self, document_id: uuid.UUID) -> None:
        """Remove the document and its file."""

    def list_for_patient(self, patient_id: uuid.UUID) -> list[MedicalDocument]:
        """Newest first."""
