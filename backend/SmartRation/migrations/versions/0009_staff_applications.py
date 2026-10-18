"""Staff applications: a citizen asks to become a shop owner or an official; only an Admin decides.

Design: docs/architecture/STAFF_ONBOARDING_DESIGN.md. Additive and non-destructive: one new table, no existing table or
row changes. Applying never changes Users.Role; approval (in the service, under row locks) does. Downgrade drops the
table and every application in it (roles already granted stay on Users), so take a backup first if any exist.

Approved by the owner 2026-10-18. Follows 0007 (the 0008 OTP-index draft is a separate, not yet approved decision).

Revision ID: 0009_staff_applications
Revises: 0007_user_totp
Create Date: 2026-10-18
"""
from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = '0009_staff_applications'
down_revision = '0007_user_totp'
branch_labels = None
depends_on = None

DT6 = sa.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql')


def _has_table() -> bool:
    # Offline mode (scripts/export_schema_sql.py writes the SQL without a database) can't look.
    if context.is_offline_mode():
        return False
    # lower(): MySQL on Windows (lower_case_table_names=1) reports table names in lower case.
    return "staffapplications" in {t.lower() for t in sa.inspect(op.get_bind()).get_table_names()}


def upgrade() -> None:
    if _has_table():
        return
    op.create_table('StaffApplications',
    sa.Column('Id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('UserId', sa.Integer(), nullable=False),
    sa.Column('RequestedRole', sa.Integer(), nullable=False),          # 2 = ShopOwner, 3 = GovernmentOfficial only
    sa.Column('RationShopId', sa.Integer(), nullable=True),            # required for ShopOwner
    sa.Column('Office', sa.String(length=200), nullable=True),         # district / office for officials
    sa.Column('Designation', sa.String(length=120), nullable=False),
    sa.Column('ProofReference', sa.String(length=120), nullable=False),  # the ID/licence number checked; no image
    sa.Column('Status', sa.Integer(), nullable=False),                 # 1 Pending, 2 Approved, 3 Rejected, 4 Withdrawn
    sa.Column('DecidedByUserId', sa.Integer(), nullable=True),
    sa.Column('DecisionReason', sa.String(length=500), nullable=True),
    sa.Column('CreatedAt', DT6, nullable=False),
    sa.Column('DecidedAt', DT6, nullable=True),
    sa.CheckConstraint('RequestedRole IN (2, 3)', name='CK_StaffApplications_RequestedRole'),
    sa.CheckConstraint('Status IN (1, 2, 3, 4)', name='CK_StaffApplications_Status'),
    sa.ForeignKeyConstraint(['UserId'], ['Users.Id'], name=op.f('FK_StaffApplications_Users_UserId'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['RationShopId'], ['RationShops.Id'], name=op.f('FK_StaffApplications_RationShops_RationShopId'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['DecidedByUserId'], ['Users.Id'], name=op.f('FK_StaffApplications_Users_DecidedByUserId'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('Id')
    )
    op.create_index('IX_StaffApplications_UserId_Status', 'StaffApplications', ['UserId', 'Status'], unique=False)
    op.create_index('IX_StaffApplications_Status_CreatedAt', 'StaffApplications', ['Status', 'CreatedAt'], unique=False)


def downgrade() -> None:
    op.drop_table('StaffApplications')
