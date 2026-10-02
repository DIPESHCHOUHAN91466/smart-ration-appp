"""AuditLogs gets an index on (UserId, CreatedAt): a person's recent actions without scanning the whole log.

Used by the per-account sign-in lockout (recent LOGIN_FAILED rows) and the audit pages. Additive and
non-destructive: one index, no data change. Downgrade drops the index.

Revision ID: 0005_audit_user_time_index
Revises: 0004_grievances
Create Date: 2026-10-02
"""
from alembic import context, op
import sqlalchemy as sa

revision = '0005_audit_user_time_index'
down_revision = '0004_grievances'
branch_labels = None
depends_on = None

INDEX = 'IX_AuditLogs_UserId_CreatedAt'


def _has_index() -> bool:
    # Offline mode (scripts/export_schema_sql.py writes the SQL without a database) can't look.
    if context.is_offline_mode():
        return False
    return INDEX in {i["name"] for i in sa.inspect(op.get_bind()).get_indexes("AuditLogs")}


def upgrade() -> None:
    if not _has_index():
        op.create_index(INDEX, 'AuditLogs', ['UserId', 'CreatedAt'], unique=False)


def downgrade() -> None:
    op.drop_index(INDEX, table_name='AuditLogs')
