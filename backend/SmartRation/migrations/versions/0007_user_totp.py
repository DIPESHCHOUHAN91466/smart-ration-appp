"""Two-factor sign-in for staff: Users gets TotpSecret (encrypted), TotpEnabledAt and TotpLastStep.

Additive and non-destructive: three nullable columns, no existing value changes (every account starts without
two-factor sign-in). Downgrade drops the columns, which turns two-factor sign-in off for everyone.

Revision ID: 0007_user_totp
Revises: 0006_password_reset_codes
Create Date: 2026-10-06
"""
from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '0007_user_totp'
down_revision = '0006_password_reset_codes'
branch_labels = None
depends_on = None

COLUMNS = ('TotpSecret', 'TotpEnabledAt', 'TotpLastStep')


def _existing() -> set[str]:
    # Offline mode (scripts/export_schema_sql.py writes the SQL without a database) can't look.
    if context.is_offline_mode():
        return set()
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns("Users")}


def upgrade() -> None:
    # A database built from the current models already has the columns.
    have = _existing()
    if 'TotpSecret' not in have:
        op.add_column('Users', sa.Column('TotpSecret', sa.String(length=255), nullable=True))
    if 'TotpEnabledAt' not in have:
        op.add_column('Users', sa.Column('TotpEnabledAt', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True))
    if 'TotpLastStep' not in have:
        op.add_column('Users', sa.Column('TotpLastStep', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=True))


def downgrade() -> None:
    for name in reversed(COLUMNS):
        op.drop_column('Users', name)
