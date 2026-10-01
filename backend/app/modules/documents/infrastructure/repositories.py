import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.modules.documents.domain.entities import MedicalDocument
from app.shared.infrastructure.mapping import copy_to_row, to_entity

from .models import DocumentFileModel, MedicalDocumentModel


class SqlAlchemyDocumentRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, document: MedicalDocument, content: bytes) -> None:
        row = MedicalDocumentModel()
        copy_to_row(document, row)
        self._session.add(row)
        self._session.flush()
        self._session.add(DocumentFileModel(document_id=document.id, content=content))
        self._session.flush()

    def get(self, document_id: uuid.UUID) -> MedicalDocument | None:
        row = self._session.get(MedicalDocumentModel, document_id)
        return to_entity(MedicalDocument, row) if row else None

    def content(self, document_id: uuid.UUID) -> bytes:
        return self._session.scalar(
            sa.select(DocumentFileModel.content).where(DocumentFileModel.document_id == document_id)
        )

    def delete(self, document_id: uuid.UUID) -> None:
        # document_files goes with it (ON DELETE CASCADE); a rehab imaging link becomes NULL.
        self._session.execute(
            sa.delete(MedicalDocumentModel).where(MedicalDocumentModel.id == document_id)
        )

    def list_for_patient(self, patient_id: uuid.UUID) -> list[MedicalDocument]:
        rows = self._session.scalars(
            sa.select(MedicalDocumentModel)
            .where(MedicalDocumentModel.patient_id == patient_id)
            .order_by(MedicalDocumentModel.created_at.desc())
        )
        return [to_entity(MedicalDocument, row) for row in rows]
