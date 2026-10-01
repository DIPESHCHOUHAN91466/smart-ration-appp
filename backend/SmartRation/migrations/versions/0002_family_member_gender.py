"""Family members get an optional Gender (Gender enum: 1 Male, 2 Female, 3 Other; NULL = not recorded).

Additive and non-destructive: one nullable column. Existing rows are filled only where the data
already says it:
  * the head of a family takes the gender recorded on that family's beneficiary;
  * Son -> Male, Daughter -> Female;
  * Spouse / Parent / Other stay NULL (not recorded) rather than guessed.

The C# API (legacy) ignores the new column. Downgrade drops the column and its values.

Revision ID: 0002_family_member_gender
Revises: 0001_initial
Create Date: 2026-10-01
"""
from alembic import context, op
import sqlalchemy as sa

revision = '0002_family_member_gender'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

HEAD, SON, DAUGHTER = 1, 3, 4      # FamilyRelationship
MALE, FEMALE = 1, 2                # Gender


def _has_gender_column() -> bool:
    # Offline mode (scripts/export_schema_sql.py writes the SQL without a database) can't look.
    if context.is_offline_mode():
        return False
    return "Gender" in {c["name"] for c in sa.inspect(op.get_bind()).get_columns("FamilyMembers")}


def upgrade() -> None:
    # A database built from the current models already has the column; only the missing values are filled.
    if not _has_gender_column():
        op.add_column('FamilyMembers', sa.Column('Gender', sa.Integer(), nullable=True))
    op.execute(f"UPDATE FamilyMembers SET Gender = {MALE} WHERE Relationship = {SON} AND Gender IS NULL")
    op.execute(f"UPDATE FamilyMembers SET Gender = {FEMALE} WHERE Relationship = {DAUGHTER} AND Gender IS NULL")
    op.execute(
        "UPDATE FamilyMembers SET Gender = ("
        " SELECT b.Gender FROM Beneficiaries b WHERE b.FamilyId = FamilyMembers.FamilyId ORDER BY b.Id LIMIT 1"
        f") WHERE Relationship = {HEAD} AND Gender IS NULL"
    )


def downgrade() -> None:
    op.drop_column('FamilyMembers', 'Gender')
