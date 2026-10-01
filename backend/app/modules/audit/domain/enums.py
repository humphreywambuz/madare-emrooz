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
    RECORD_CREATED = "record_created"  # e.g. a daily log written by the midwife
    STAFF_ACCOUNT_CREATED = "staff_account_created"
    STAFF_ACCOUNT_UPDATED = "staff_account_updated"
    MIDWIFE_CHOSEN = "midwife_chosen"
    ALERT_SEEN = "alert_seen"
    PARTNER_LINK_CREATED = "partner_link_created"
    PARTNER_LINK_REVOKED = "partner_link_revoked"
    PARTNER_LINK_VIEWED = "partner_link_viewed"
