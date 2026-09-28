"""Write database/schema/smartration_schema.sql: the MySQL DDL of the Alembic migrations, for reading.

The schema is owned by the Alembic migrations (backend/SmartRation/migrations). This file is a generated, read-only
snapshot for people who want to see the tables as SQL (reviews, DBAs, documentation). It never
connects to a database (Alembic "offline" mode) and contains no credentials.

    .venv\\Scripts\\python scripts\\export_schema_sql.py           # rewrite the snapshot
    .venv\\Scripts\\python scripts\\export_schema_sql.py --check   # exit 1 if the snapshot is out of date

tests/test_schema_snapshot.py runs --check, so a migration without a refreshed snapshot fails the tests.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from _common import alembic_config
from alembic import command

OUTPUT = Path(__file__).resolve().parents[3] / "database" / "schema" / "smartration_schema.sql"
HEADER = """-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations (Alembic).
-- Regenerate: cd backend/SmartRation; .venv\\Scripts\\python scripts\\export_schema_sql.py
-- MySQL 8 (tables use the database defaults: InnoDB, utf8mb4). Apply schema changes with `alembic upgrade head`, never with this file.

"""


def render() -> str:
    cfg = alembic_config()
    buffer = io.StringIO()
    cfg.output_buffer = buffer
    # A URL is only needed to pick the MySQL dialect; offline mode never connects.
    cfg.attributes["database_url"] = "mysql+pymysql://schema@localhost/smartration"
    command.upgrade(cfg, "head", sql=True)
    lines = [line.rstrip() for line in buffer.getvalue().splitlines()]
    return HEADER + "\n".join(lines).strip() + "\n"


def main() -> int:
    sql = render()
    if "--check" in sys.argv:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != sql:
            print(f"{OUTPUT} is out of date: run scripts/export_schema_sql.py")
            return 1
        print("Schema snapshot is up to date.")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(sql, encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT} ({sql.count('CREATE TABLE')} tables)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
