from enum import StrEnum


class DocumentType(StrEnum):
    BLOOD_TEST = "blood_test"
    URINE_TEST = "urine_test"
    THYROID_TEST = "thyroid_test"
    ULTRASOUND = "ultrasound"
    SCREENING = "screening"
    IMAGING = "imaging"  # radiology / MRI (orthopedic referral)
    OTHER = "other"
