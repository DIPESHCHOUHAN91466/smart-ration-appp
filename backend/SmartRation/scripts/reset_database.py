"""DESTROY and recreate the Smart Ration schema. Development/test only.

Safety rails, all required:
  * RESET_DATABASE=true and CONFIRM_RESET=SMART_RATION_RESET in the environment
  * ENVIRONMENT (or APP_ENV) must not be "production"
  * you must type the database name when prompted (or pass --yes-i-typed-it <name>)
  * a backup is taken first (database/mysql/backup.ps1) unless --skip-backup;
    if the backup fails, nothing is dropped.

Then: alembic downgrade base -> upgrade head -> seed -> verify.

Usage (from backend/SmartRation):
    $env:RESET_DATABASE="true"; $env:CONFIRM_RESET="SMART_RATION_RESET"
    .venv\\Scripts\\python scripts\\reset_database.py
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

import seed_database
import verify_database
from _common import ROOT, alembic_config, database_name, database_url, safe_url
from alembic import command

from app.core.config import get_settings

BACKUP_SCRIPT = ROOT.parents[1] / "database" / "mysql" / "backup.ps1"


def take_backup(url: str) -> None:
    from sqlalchemy.engine import make_url

    u = make_url(url)
    env = dict(os.environ, SMARTRATION_DB_USER=u.username or "", SMARTRATION_DB_PASSWORD=u.password or "")
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(BACKUP_SCRIPT),
         "-Database", u.database or "", "-DbHost", u.host or "localhost", "-Port", str(u.port or 3306)],
        env=env, capture_output=True, text=True,
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        raise SystemExit(f"Backup failed; nothing was dropped.\n{result.stderr.strip()}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Drop and recreate the schema (dev/test only).")
    parser.add_argument("--skip-backup", action="store_true")
    parser.add_argument("--no-seed", action="store_true")
    parser.add_argument("--yes-i-typed-it", metavar="DATABASE", help="non-interactive confirmation: the database name")
    args = parser.parse_args()

    if os.environ.get("RESET_DATABASE") != "true" or os.environ.get("CONFIRM_RESET") != "SMART_RATION_RESET":
        print("Refusing: set RESET_DATABASE=true and CONFIRM_RESET=SMART_RATION_RESET.")
        return 1
    if "production" in {get_settings().environment.lower(), os.environ.get("APP_ENV", "").lower()}:
        print("Refusing: the environment is production.")
        return 1

    url = database_url()
    name = database_name(url)
    print(f"This will DELETE ALL DATA in {safe_url(url)}.")
    typed = args.yes_i_typed_it if args.yes_i_typed_it is not None else input(f"Type the database name ({name}) to continue: ")
    if typed.strip() != name:
        print("Name did not match; nothing changed.")
        return 1

    if url.startswith("mysql") and not args.skip_backup:
        take_backup(url)

    cfg = alembic_config()
    command.downgrade(cfg, "base")  # the migration re-checks the two env flags itself
    command.upgrade(cfg, "head")
    if not args.no_seed:
        seed_database.main()
    errors = verify_database.run(allow_unstamped=False)
    print("DATABASE VERIFICATION " + ("FAILED\n  - " + "\n  - ".join(errors) if errors else "PASSED"))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
