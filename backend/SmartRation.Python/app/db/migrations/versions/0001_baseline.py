"""Baseline: the existing MySQL schema created by EF Core (InitialMySql, 2026-09-24).

This revision intentionally does NOTHING. It marks the starting point so that
future Alembic revisions build on the schema as it already exists. It must
never create or drop tables: existing data is preserved.

Adopting Alembic on an existing database (only when Python takes over schema
ownership; not during Step 1):
    1. Back up:   mysqldump --single-transaction smartration > backup.sql
    2. Verify:    pytest tests/test_schema_compat.py   (models == live schema)
    3. Stamp:     alembic stamp baseline               (adds the alembic_version table only)

Revision ID: baseline
Revises:
Create Date: 2026-09-24
"""

revision = "baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
