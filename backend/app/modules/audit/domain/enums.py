from enum import StrEnum


class AuditEventType(StrEnum):
    PROFILE_CREATED = "profile_created"
    RECORD_VIEWED = "record_viewed"
    RECORD_UPDATED = "record_updated"
    ACCESS_DENIED = "access_denied"
    LOGIN_SUCCEEDED = "login_succeeded"
    LOGIN_FAILED = "login_failed"
    DOCUMENT_UPLOADED = "document_uploaded"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REVOKED = "approval_revoked"
