"""Citizens' grievances (complaints), each with a reference number such as GRV-2026-000123.

Additive and non-destructive: one new table; no existing table or row changes.
The C# API (legacy) does not know the table and is unaffected. Downgrade drops the table and every
grievance in it, so take a backup first if any real complaints were recorded.

Revision ID: 0004_grievances
Revises: 0003_stock_movement_keys
Create Date: 2026-10-02
"""
from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '0004_grievances'
down_revision = '0003_stock_movement_keys'
branch_labels = None
depends_on = None


def _has_table() -> bool:
    # Offline mode (scripts/export_schema_sql.py writes the SQL without a database) can't look.
    if context.is_offline_mode():
        return False
    return "Grievances" in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    # A database built from the current models already has the table.
    if _has_table():
        return
    op.create_table('Grievances',
    sa.Column('Id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('ReferenceNumber', sa.String(length=32), nullable=False),
    sa.Column('UserId', sa.Integer(), nullable=False),
    sa.Column('RationShopId', sa.Integer(), nullable=True),
    sa.Column('Category', sa.Integer(), nullable=False),
    sa.Column('RationType', sa.Integer(), nullable=True),
    sa.Column('Description', sa.String(length=1000), nullable=False),
    sa.Column('Status', sa.Integer(), nullable=False),
    sa.Column('Source', sa.String(length=16), server_default='APP', nullable=False),
    sa.Column('IdempotencyKey', sa.String(length=64), nullable=True),
    sa.Column('ResolutionNote', sa.String(length=500), nullable=True),
    sa.Column('ResolvedByUserId', sa.Integer(), nullable=True),
    sa.Column('CreatedAt', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.Column('UpdatedAt', sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql'), nullable=False),
    sa.ForeignKeyConstraint(['UserId'], ['Users.Id'], name=op.f('FK_Grievances_Users_UserId'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['RationShopId'], ['RationShops.Id'], name=op.f('FK_Grievances_RationShops_RationShopId'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('Id')
    )
    op.create_index('IX_Grievances_ReferenceNumber', 'Grievances', ['ReferenceNumber'], unique=True)
    op.create_index('IX_Grievances_IdempotencyKey', 'Grievances', ['IdempotencyKey'], unique=True)
    op.create_index('IX_Grievances_UserId_CreatedAt', 'Grievances', ['UserId', 'CreatedAt'], unique=False)
    op.create_index('IX_Grievances_Status_CreatedAt', 'Grievances', ['Status', 'CreatedAt'], unique=False)
    op.create_index('IX_Grievances_RationShopId_Status', 'Grievances', ['RationShopId', 'Status'], unique=False)


def downgrade() -> None:
    op.drop_table('Grievances')
