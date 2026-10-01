"""Medical document use cases. Only the mother's midwife uploads; the file is stored in the database.

Depend only on ports, never on Flask or SQLAlchemy.
"""
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal

from app.modules.audit.application.trail import AuditEvent, AuditTrail
from app.modules.audit.domain.enums import AuditEventType
from app.modules.documents.domain.entities import (
    MedicalDocument,
    clean_filename,
    detect_content_type,
)
from app.modules.documents.domain.enums import DocumentType
from app.shared.application.access import PatientAccess
from app.shared.application.context import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import NotFoundError, ValidationError

from .ports import DocumentRepository

MAX_FILE_BYTES = 10 * 1024 * 1024


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DocumentService:
    def __init__(
        self,
        *,
        documents: DocumentRepository,
        active_pregnancy_id: Callable[[uuid.UUID], uuid.UUID | None],
        access: PatientAccess,
        audit: AuditTrail,
        uow: UnitOfWork,
        max_file_bytes: int = MAX_FILE_BYTES,
        now: Callable[[], datetime] = _utcnow,
    ):
        self._documents = documents
        self._active_pregnancy_id = active_pregnancy_id
        self._access = access
        self._audit = audit
        self._uow = uow
        self._max_file_bytes = max_file_bytes
        self._now = now

    def upload(
        self,
        actor: Actor,
        patient_id: uuid.UUID,
        *,
        filename: str | None,
        content: bytes,
        document_type: DocumentType,
        performed_at: datetime | None = None,
        fundal_height_cm: Decimal | None = None,
        fetal_heart_rate_bpm: int | None = None,
        notes: str | None = None,
    ) -> MedicalDocument:
        self._access.require_record_access(actor, patient_id)
        if not content:
            raise ValidationError("Choose a file to upload.", details={"field": "file"})
        if len(content) > self._max_file_bytes:
            raise ValidationError(
                f"Files can be at most {self._max_file_bytes // (1024 * 1024)} MB.",
                details={"field": "file"},
            )
        content_type = detect_content_type(content)
        if content_type is None:
            raise ValidationError("Upload a JPEG, PNG or PDF file.", details={"field": "file"})
        document = MedicalDocument(
            patient_id=patient_id,
            uploaded_by_id=actor.user_id,
            document_type=document_type,
            original_filename=clean_filename(filename),
            content_type=content_type,
            file_size_bytes=len(content),
            created_at=self._now(),
            pregnancy_id=self._active_pregnancy_id(patient_id),
            performed_at=performed_at,
            fundal_height_cm=fundal_height_cm,
            fetal_heart_rate_bpm=fetal_heart_rate_bpm,
            notes=notes,
        )
        self._documents.add(document, content)
        self._audit.record(
            AuditEvent(
                AuditEventType.DOCUMENT_UPLOADED,
                actor_id=actor.user_id,
                patient_id=patient_id,
                resource_type="medical_document",
                resource_id=str(document.id),
                ip_address=actor.context.ip_address,
                user_agent=actor.context.user_agent,
                details={"document_type": document_type.value, "size": len(content)},
            )
        )
        self._uow.commit()
        return document

    def documents_for_patient(self, actor: Actor, patient_id: uuid.UUID) -> list[MedicalDocument]:
        self._access.require_record_access(actor, patient_id)
        documents = self._documents.list_for_patient(patient_id)
        self._access.record_viewed(actor, patient_id, "medical_documents")
        return documents

    def file_for_patient(
        self, actor: Actor, patient_id: uuid.UUID, document_id: uuid.UUID
    ) -> tuple[MedicalDocument, bytes]:
        self._access.require_record_access(actor, patient_id)
        document, content = self._load(patient_id, document_id)
        self._access.record_viewed(actor, patient_id, "medical_document", document_id)
        return document, content

    def own_documents(self, user_id: uuid.UUID) -> list[MedicalDocument]:
        return self._documents.list_for_patient(user_id)

    def own_file(self, user_id: uuid.UUID, document_id: uuid.UUID) -> tuple[MedicalDocument, bytes]:
        return self._load(user_id, document_id)

    def require_document_of(self, patient_id: uuid.UUID, document_id: uuid.UUID) -> MedicalDocument:
        document = self._documents.get(document_id)
        if document is None or document.patient_id != patient_id:
            raise NotFoundError("Document not found.")
        return document

    def _load(self, patient_id: uuid.UUID, document_id: uuid.UUID) -> tuple[MedicalDocument, bytes]:
        document = self.require_document_of(patient_id, document_id)
        return document, self._documents.content(document_id)
