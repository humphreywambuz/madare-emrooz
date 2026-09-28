from app.modules.documents.domain.enums import DocumentType
from app.modules.documents.infrastructure.models import MedicalDocumentModel


def test_medical_document(session, make_user):
    user = make_user()
    doc = MedicalDocumentModel(
        patient_id=user.id,
        uploaded_by_id=user.id,
        document_type=DocumentType.ULTRASOUND,
        storage_key="patients/abc/ultrasound-1.pdf",
        original_filename="ultrasound.pdf",
        content_type="application/pdf",
        file_size_bytes=2048,
        fetal_heart_rate_bpm=140,
    )
    session.add(doc)
    session.flush()
    assert doc.id is not None
