"""Verify the Smart Ration database. Read-only.

Checks: connectivity, expected database name, MySQL version, every expected
table/column/type/nullability/default/foreign key/index/unique constraint
(Alembic's own comparison against the SQLAlchemy models), migration version,
and that the reference/seed records exist.

Usage (from backend/SmartRation):
    .venv\\Scripts\\python scripts\\verify_database.py
    .venv\\Scripts\\python scripts\\verify_database.py --allow-unstamped   # before setup_database.py adopts it
Exit code 0 = passed, 1 = failed.
"""

from __future__ import annotations

import argparse
import sys

from _common import (
    EXPECTED_DATABASE,
    LEGACY_MARKER_TABLE,
    alembic_head,
    current_revision,
    database_name,
    database_url,
    engine,
    model_tables,
    safe_url,
    table_names,
)
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import SQLAlchemyError

from app.database.base import Base
from app.database.models import Inventory, RationItem, RationScheme, RationShop, SchemeEntitlementItem, User
from app.database.schema_utils import comparable_metadata

IGNORED = {LEGACY_MARKER_TABLE, "alembic_version"}


def run(allow_unstamped: bool) -> list[str]:
    errors: list[str] = []
    url = database_url()
    print(f"Database: {safe_url(url)}")

    name = database_name(url)
    if url.startswith("mysql") and name != EXPECTED_DATABASE:
        errors.append(f"Connected to database '{name}', expected '{EXPECTED_DATABASE}'.")

    eng = engine()
    try:
        with eng.connect() as conn:
            if conn.dialect.name == "mysql":
                version = conn.execute(text("SELECT VERSION()")).scalar()
                print(f"MySQL {version}")
                if not str(version).startswith("8."):
                    errors.append(f"MySQL 8.x required, found {version}.")
    except SQLAlchemyError as exc:
        return [f"Cannot connect: {type(exc).__name__}: {str(exc).splitlines()[0][:200]}"]

    # Tables
    present = table_names(eng)
    missing = model_tables() - present
    unexpected = present - model_tables() - IGNORED
    if missing:
        errors.append(f"Missing tables: {sorted(missing)}")
    if unexpected:
        errors.append(f"Unexpected tables: {sorted(unexpected)}")
    print(f"Tables: {len(present - IGNORED)} present, {len(model_tables())} expected")

    # Columns, types, nullability, defaults, FKs, indexes, unique constraints
    if not missing:
        with eng.connect() as conn:
            ctx = MigrationContext.configure(conn, opts={
                "compare_type": True,
                "compare_server_default": True,
                "include_object": lambda obj, n, type_, reflected, compare_to: not (type_ == "table" and n.lower() in IGNORED),
            })
            drift = compare_metadata(ctx, comparable_metadata(conn, Base.metadata))
        for item in drift[:25]:
            errors.append(f"Schema drift: {item}")
        insp = inspect(eng)
        fk_count = sum(len(insp.get_foreign_keys(t)) for t in insp.get_table_names() if t.lower() not in IGNORED)
        idx_count = sum(len(insp.get_indexes(t)) for t in insp.get_table_names() if t.lower() not in IGNORED)
        uq_count = sum(1 for t in insp.get_table_names() if t.lower() not in IGNORED for i in insp.get_indexes(t) if i["unique"])
        print(f"Foreign keys: {fk_count} · indexes: {idx_count} (unique: {uq_count}) · drift: {len(drift)}")

    # Migration state
    head, current = alembic_head(), current_revision(eng)
    print(f"Alembic: current={current} head={head}")
    if current != head:
        if current is None and allow_unstamped:
            print("  (not stamped yet — allowed by --allow-unstamped)")
        else:
            errors.append(f"Migration version is {current}, expected {head}. Run scripts/setup_database.py.")

    # Reference / seed records
    if not missing:
        from sqlalchemy.orm import Session

        with Session(eng) as db:
            counts = {
                "ration items": db.scalar(select(func.count()).select_from(RationItem)),
                "ration schemes": db.scalar(select(func.count()).select_from(RationScheme)),
                "scheme entitlements": db.scalar(select(func.count()).select_from(SchemeEntitlementItem)),
                "ration shops": db.scalar(select(func.count()).select_from(RationShop)),
                "inventory rows": db.scalar(select(func.count()).select_from(Inventory)),
                "users": db.scalar(select(func.count()).select_from(User)),
            }
        print("Seed records: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
        for label, n in counts.items():
            if not n:
                errors.append(f"No {label} found. Run scripts/seed_database.py.")
    eng.dispose()
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the Smart Ration database (read-only).")
    parser.add_argument("--allow-unstamped", action="store_true", help="don't fail when Alembic hasn't adopted the database yet")
    args = parser.parse_args()
    errors = run(args.allow_unstamped)
    if errors:
        print("\nDATABASE VERIFICATION FAILED")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("\nDATABASE VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
