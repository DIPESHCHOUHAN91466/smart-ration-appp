"""Prepare the Smart Ration database. Never drops or rewrites existing data.

  1. Check connectivity and that we're connected to the expected database.
  2. Decide from the current state:
     * empty database                          -> `alembic upgrade head` (creates every table)
     * already managed by Alembic               -> `alembic upgrade head` (applies pending migrations)
     * existing C#/EF Core database, no Alembic -> verify it matches the models exactly,
                                                   then `alembic stamp 0001_initial` + upgrade
     * anything else (partial/unknown schema)   -> refuse and explain
  3. Optionally seed synthetic data (--seed), then run the verification.

Take a backup first on any database holding real data (database/mysql/backup.ps1).

Usage (from backend/SmartRation.Python):
    .venv\\Scripts\\python scripts\\setup_database.py [--seed]
"""

from __future__ import annotations

import argparse
import sys

from _common import (
    EXPECTED_DATABASE,
    LEGACY_MARKER_TABLE,
    alembic_config,
    alembic_head,
    current_revision,
    database_name,
    database_url,
    engine,
    model_tables,
    safe_url,
    table_names,
)
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy.exc import SQLAlchemyError

import seed_database
import verify_database
from app.db.database import Base
from app.db.schema_utils import comparable_metadata

BASELINE = "0001_initial"


def schema_drift(eng) -> list:
    with eng.connect() as conn:
        ctx = MigrationContext.configure(conn, opts={
            "compare_type": True,
            "compare_server_default": True,
            "include_object": lambda obj, n, type_, r, c: not (type_ == "table" and n.lower() in {LEGACY_MARKER_TABLE, "alembic_version"}),
        })
        return compare_metadata(ctx, comparable_metadata(conn, Base.metadata))


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or adopt the Smart Ration database (non-destructive).")
    parser.add_argument("--seed", action="store_true", help="insert synthetic reference/demo data into empty tables")
    args = parser.parse_args()

    url = database_url()
    print(f"Database: {safe_url(url)}")
    if url.startswith("mysql") and database_name(url) != EXPECTED_DATABASE:
        print(f"Refusing: DATABASE_URL points at '{database_name(url)}', expected '{EXPECTED_DATABASE}'.")
        return 1

    eng = engine()
    try:
        present = table_names(eng)
        revision = current_revision(eng)
    except SQLAlchemyError as exc:
        print(f"Cannot connect: {type(exc).__name__}: {str(exc).splitlines()[0][:200]}")
        print("Is MySQL running, does the database exist and are the credentials in .env right?")
        return 1
    app_tables = present - {LEGACY_MARKER_TABLE, "alembic_version"}
    cfg = alembic_config()

    if revision:
        print(f"Managed by Alembic at {revision}; head is {alembic_head()}. Applying pending migrations.")
        command.upgrade(cfg, "head")
    elif not app_tables:
        print("Empty database. Creating the schema (alembic upgrade head).")
        command.upgrade(cfg, "head")
    elif app_tables == model_tables():
        drift = schema_drift(eng)
        if drift:
            print("Refusing to adopt: the existing schema differs from the models:")
            for d in drift[:25]:
                print(f"  - {d}")
            return 1
        print(f"Existing schema (created by the C# API) matches the models exactly. Adopting it: alembic stamp {BASELINE}.")
        print("(Only the alembic_version table is added; no data or tables are changed.)")
        command.stamp(cfg, BASELINE)
        command.upgrade(cfg, "head")
    else:
        missing, extra = sorted(model_tables() - app_tables), sorted(app_tables - model_tables())
        print("Refusing: the database holds a partial or unknown schema, not managed by Alembic.")
        print(f"  missing tables: {missing}\n  unexpected tables: {extra}")
        print("Restore a backup or fix it manually; nothing was changed.")
        return 1
    eng.dispose()

    if args.seed:
        seed_database.main()

    print()
    errors = verify_database.run(allow_unstamped=False)
    if errors:
        print("DATABASE VERIFICATION FAILED")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("DATABASE VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
