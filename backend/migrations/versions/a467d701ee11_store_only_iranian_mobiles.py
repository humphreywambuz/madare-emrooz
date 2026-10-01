"""store only iranian mobiles

Revision ID: a467d701ee11
Revises: 1bcb00ce0bbf
Create Date: 2026-10-01 05:46:28.576958

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'a467d701ee11'
down_revision = '1bcb00ce0bbf'
branch_labels = None
depends_on = None


# Mobiles are stored as +98 followed by a 10-digit number starting with 9
# (see app.modules.identity.domain.mobile.IRANIAN_MOBILE_PATTERN).
IRANIAN_MOBILE = r"mobile ~ '^\+989[0-9]{9}$'"
E164 = r"mobile ~ '^\+[1-9][0-9]{7,14}$'"


def upgrade():
    # Fails if a stored number doesn't match; the app has always saved +98 numbers.
    op.drop_constraint(op.f("ck_users_mobile_e164"), "users", type_="check")
    op.create_check_constraint(op.f("ck_users_mobile_iranian"), "users", IRANIAN_MOBILE)
    op.create_check_constraint(op.f("ck_otp_codes_mobile_iranian"), "otp_codes", IRANIAN_MOBILE)


def downgrade():
    op.drop_constraint(op.f("ck_otp_codes_mobile_iranian"), "otp_codes", type_="check")
    op.drop_constraint(op.f("ck_users_mobile_iranian"), "users", type_="check")
    op.create_check_constraint(op.f("ck_users_mobile_e164"), "users", E164)
