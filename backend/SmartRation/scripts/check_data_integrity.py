"""Run the read-only data-integrity checks in database/queries against DATABASE_URL.

    .venv\\Scripts\\python scripts\\check_data_integrity.py            # the database in .env
    .venv\\Scripts\\python scripts\\check_data_integrity.py --strict   # warnings also fail

Prints each check with its violation count and up to five row ids (never personal values).
Exit code: 0 = no errors, 1 = at least one error-severity check found rows (or a warning with --strict),
2 = the checks or the database could not be read. Nothing is ever written.
"""

from __future__ import annotations

import argparse
import sys

from _common import database_url, engine, safe_url
from sqlalchemy.exc import SQLAlchemyError

from app.database.integrity import InvalidCheck, load_checks, run_checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only data-integrity checks (database/queries/*.sql).")
    parser.add_argument("--strict", action="store_true", help="fail on warnings too")
    args = parser.parse_args(argv)

    try:
        checks = load_checks()
    except InvalidCheck as exc:
        print(f"[FAIL] invalid check: {exc}")
        return 2
    print(f"Database: {safe_url(database_url())}  ({len(checks)} checks, read-only)")
    try:
        results = run_checks(engine(), checks)
    except SQLAlchemyError as exc:
        print(f"[FAIL] database error: {type(exc).__name__}")
        return 2

    failing = 0
    for r in results:
        if not r.failed:
            label = "PASS"
        elif r.check.severity == "error":
            label = "FAIL"
        else:
            label = "WARNING"
        ids = f"  ids: {', '.join(r.sample_ids)}{' ...' if r.violations > len(r.sample_ids) else ''}" if r.failed else ""
        print(f"[{label}] {r.check.name}: {r.violations}{ids}")
        if r.failed and (r.check.severity == "error" or args.strict):
            failing += 1
    print("Integrity OK" if not failing else f"{failing} check(s) failed")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
