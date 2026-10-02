"""Stock movements get an optional IdempotencyKey, so a retried delivery or write-off is recorded once.

Additive and non-destructive: one nullable column and a unique index on it. Existing rows keep NULL
(MySQL allows any number of NULLs in a unique index). Requests without the header behave as before.

The C# API (legacy) ignores the new column. Downgrade drops the index and the column (the keys only
matter for retries in flight, so nothing of lasting value is lost).

Revision ID: 0003_stock_movement_keys
Revises: 0002_family_member_gender
Create Date: 2026-10-02
"""
from alembic import context, op
import sqlalchemy as sa

revision = '0003_stock_movement_keys'
down_revision = '0002_family_member_gender'
branch_labels = None
depends_on = None


def _has_key_column() -> bool:
    # Offline mode (scripts/export_schema_sql.py writes the SQL without a database) can't look.
    if context.is_offline_mode():
        return False
    return "IdempotencyKey" in {c["name"] for c in sa.inspect(op.get_bind()).get_columns("InventoryMovements")}


def upgrade() -> None:
    # A database built from the current models already has the column and index.
    if not _has_key_column():
        op.add_column('InventoryMovements', sa.Column('IdempotencyKey', sa.String(length=64), nullable=True))
        op.create_index('IX_InventoryMovements_IdempotencyKey', 'InventoryMovements', ['IdempotencyKey'], unique=True)


def downgrade() -> None:
    op.drop_index('IX_InventoryMovements_IdempotencyKey', table_name='InventoryMovements')
    op.drop_column('InventoryMovements', 'IdempotencyKey')
