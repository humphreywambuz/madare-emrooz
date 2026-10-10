"""Refresh token generations, and the audit event for a reused refresh token.

Revision ID: 398e9e399d54
Revises: 32eb077dac4a
Create Date: 2026-10-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# Audit event types are stored as VARCHAR with a CHECK constraint; listed here so this
# migration keeps meaning the same thing if the enum changes later.
OLD_AUDIT_EVENTS = (
    "profile_created", "record_viewed", "record_updated", "access_denied", "login_succeeded",
    "login_failed", "document_uploaded", "approval_granted", "approval_revoked",
    "record_created", "staff_account_created", "staff_account_updated", "midwife_chosen",
    "alert_seen", "partner_link_created", "partner_link_revoked", "partner_link_viewed",
    "alert_raised", "document_deleted",
)
NEW_AUDIT_EVENTS = OLD_AUDIT_EVENTS + ("refresh_token_reused",)


def _audit_event_check(values) -> None:
    op.drop_constraint(op.f("ck_audit_logs_event_type_valid"), "audit_logs", type_="check")
    allowed = ", ".join(f"'{v}'" for v in values)
    op.create_check_constraint(
        op.f("ck_audit_logs_event_type_valid"), "audit_logs", f"event_type IN ({allowed})"
    )


# revision identifiers, used by Alembic.
revision = '398e9e399d54'
down_revision = '32eb077dac4a'
branch_labels = None
depends_on = None


def upgrade():
    # Sessions opened before this keep their random token until their next renewal.
    with op.batch_alter_table('user_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('refresh_generation', sa.Integer(), server_default='0', nullable=False))
    _audit_event_check(NEW_AUDIT_EVENTS)


def downgrade():
    # Fails if the log already holds the new event type: audit rows are never deleted.
    _audit_event_check(OLD_AUDIT_EVENTS)
    with op.batch_alter_table('user_sessions', schema=None) as batch_op:
        batch_op.drop_column('refresh_generation')
