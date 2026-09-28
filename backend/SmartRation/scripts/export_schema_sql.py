"""Write the MySQL SQL generated from the Alembic migrations, for reading and for DBAs.

  database/schema/smartration_schema.sql        the whole schema at head (every table, key and index)
  database/migrations/<revision>.upgrade.sql    what each revision changes, in order
  database/migrations/<revision>.downgrade.sql  how to undo it (not for the initial revision: undoing it would drop
                                                every table, which the migration refuses — restore a backup instead)

The schema is owned by the Alembic migrations (backend/SmartRation/migrations). These files are generated,
read-only views for reviews, documentation, and databases where schema changes must be applied by a DBA as
SQL. The script never connects to a database (Alembic "offline" mode) and writes no credentials.

    .venv\\Scripts\\python scripts\\export_schema_sql.py           # rewrite every file
    .venv\\Scripts\\python scripts\\export_schema_sql.py --check   # exit 1 if any file is out of date

tests/integration/test_schema_snapshot.py runs --check, so a migration without refreshed files fails the tests.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from _common import alembic_config
from alembic import command
from alembic.script import ScriptDirectory

DATABASE_DIR = Path(__file__).resolve().parents[3] / "database"
OUTPUT = DATABASE_DIR / "schema" / "smartration_schema.sql"
MIGRATIONS_OUTPUT = DATABASE_DIR / "migrations"
HEADER = """-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations (Alembic).
-- Regenerate: cd backend/SmartRation; .venv\\Scripts\\python scripts\\export_schema_sql.py
-- MySQL 8 (tables use the database defaults: InnoDB, utf8mb4). Apply schema changes with `alembic upgrade head`, never with this file.

"""
REVISION_HEADER = """-- GENERATED FILE - do not edit. Source of truth: backend/SmartRation/migrations/versions (Alembic revision {revision}).
-- Regenerate: cd backend/SmartRation; .venv\\Scripts\\python scripts\\export_schema_sql.py
-- {direction} {span}, MySQL 8. Prefer `alembic {verb} {target}`; if a DBA must apply SQL by hand, take a backup first
-- (scripts/database/backup.ps1) and apply this whole file, which also updates alembic_version.

"""


def _offline(run) -> str:
    cfg = alembic_config()
    buffer = io.StringIO()
    cfg.output_buffer = buffer
    # A URL is only needed to pick the MySQL dialect; offline mode never connects.
    cfg.attributes["database_url"] = "mysql+pymysql://schema@localhost/smartration"
    run(cfg)
    return "\n".join(line.rstrip() for line in buffer.getvalue().splitlines()).strip() + "\n"


def render() -> str:
    return HEADER + _offline(lambda cfg: command.upgrade(cfg, "head", sql=True))


def render_revisions() -> dict[str, str]:
    """{file name: SQL} for every revision: its upgrade, and its downgrade unless it is the initial revision."""
    files: dict[str, str] = {}
    for script in ScriptDirectory.from_config(alembic_config()).walk_revisions():
        rev, down = script.revision, script.down_revision
        if not isinstance(down, str | None):
            raise SystemExit(f"revision {rev} merges branches; export it by hand")
        start = down or "base"
        files[f"{rev}.upgrade.sql"] = REVISION_HEADER.format(
            revision=rev, direction="Upgrade", span=f"{start} -> {rev}", verb="upgrade", target=rev,
        ) + _offline(lambda cfg, s=start, r=rev: command.upgrade(cfg, f"{s}:{r}" if s != "base" else r, sql=True))
        if down is None:
            continue
        files[f"{rev}.downgrade.sql"] = REVISION_HEADER.format(
            revision=rev, direction="Downgrade", span=f"{rev} -> {start}", verb="downgrade", target=start,
        ) + _offline(lambda cfg, s=start, r=rev: command.downgrade(cfg, f"{r}:{s}", sql=True))
    return files


def expected_files() -> dict[Path, str]:
    files = {OUTPUT: render()}
    files.update({MIGRATIONS_OUTPUT / name: sql for name, sql in render_revisions().items()})
    return files


def main() -> int:
    expected = expected_files()
    stale_generated = {p for p in MIGRATIONS_OUTPUT.glob("*.sql")} - set(expected)
    if "--check" in sys.argv:
        out_of_date = [p for p, sql in expected.items() if not p.exists() or p.read_text(encoding="utf-8") != sql]
        problems = [f"{p} is out of date" for p in out_of_date] + [f"{p} has no Alembic revision" for p in sorted(stale_generated)]
        if problems:
            print("\n".join(problems) + "\nRun scripts/export_schema_sql.py")
            return 1
        print(f"Schema snapshot and {len(expected) - 1} migration SQL files are up to date.")
        return 0
    for path, sql in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(sql, encoding="utf-8", newline="\n")
    for path in stale_generated:
        path.unlink()  # a revision was removed from Alembic; its generated SQL goes too
    print(f"Wrote {OUTPUT} ({expected[OUTPUT].count('CREATE TABLE')} tables) and {len(expected) - 1} files in {MIGRATIONS_OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
