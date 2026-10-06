"""One-time password-reset codes (sent to the registered mobile; only a SHA-256 is stored).

Additive and non-destructive: one new table; no existing table or row changes. Downgrade drops the table
(only short-lived reset codes are lost).

Revision ID: 0006_password_reset_codes
Revises: 0005_audit_user_time_index
Create Date: 2026-10-06
"""
from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '0006_password_reset_codes'
down_revision = '0005_audit_user_time_index'
branch_labels = None
depends_on = None


def _has_table() -> bool:
    # Offline mode (scripts/export_schema_sql.py writes the SQL without a database) can't look.
    if context.is_offline_mode():
        return False
    return "PasswordResetCodes" in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    # A database built from the current models already has the table.
    if _has_table():
        return
    op.create_table('PasswordResetCodes',
    sa.Column('Id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('UserId', sa.Integer(), nullable=False),
    sa.Column('CodeHash', sa.String(length=64), nullable=False),
    sa.Column('AttemptCount', sa.Integer(), nullable=False),
    sa.Column('MaxAttempts', sa.Integer(), nullable=False),
    sa.Column('Status', sa.Integer(), nullable=False),
    sa.Column('CreatedAt', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('ExpiresAt', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('UsedAt', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=True),
    sa.ForeignKeyConstraint(['UserId'], ['Users.Id'], name=op.f('FK_PasswordResetCodes_Users_UserId'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('Id')
    )
    op.create_index('IX_PasswordResetCodes_UserId_CreatedAt', 'PasswordResetCodes', ['UserId', 'CreatedAt'], unique=False)


def downgrade() -> None:
    op.drop_table('PasswordResetCodes')
