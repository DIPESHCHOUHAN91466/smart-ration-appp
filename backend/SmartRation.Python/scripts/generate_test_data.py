"""Generate deterministic SYNTHETIC citizens (app/synthetic) and optionally insert them into the TEST database.

Usage (from backend/SmartRation.Python):
    .venv\\Scripts\\python scripts\\generate_test_data.py --users 1000                 # generate + validate, print a summary
    .venv\\Scripts\\python scripts\\generate_test_data.py --users 1000 --json out.json # also write the records as JSON
    .venv\\Scripts\\python scripts\\generate_test_data.py --users 1000 --insert        # insert into smartration_test
    .venv\\Scripts\\python scripts\\generate_test_data.py --users 1000 --insert --bookings  # + one upcoming token each
    .venv\\Scripts\\python scripts\\generate_test_data.py --users 1000 --insert --bookings --collections 0.5  # + past collections

--seed (default 2026, or the SEED environment variable) makes the output reproducible.
--insert only ever writes to a database whose name ends in _test (DATABASE_URL from .env with the
name swapped, or TEST_DATABASE_URL), only when DATA_MODE=synthetic, and in one transaction.
Generated accounts can't log in unless SYNTHETIC_USER_PASSWORD is set (the password is never printed).
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import secrets
import sys
import time
from datetime import date

from _common import database_url, safe_url
from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.models import RationShop
from app.synthetic import SyntheticDataError, book, collect, generate, insert, validate


def _test_url(name: str) -> str:
    url = os.environ.get("TEST_DATABASE_URL") or make_url(database_url()).set(database=name).render_as_string(hide_password=False)
    if not (make_url(url).database or "").endswith("_test"):
        raise SystemExit(f"Refusing: '{make_url(url).database}' does not end in _test. Synthetic bulk data only goes into a test database.")
    return url


def _json_default(value):
    if isinstance(value, date):
        return value.isoformat()
    if hasattr(value, "name"):          # enums
        return value.name
    raise TypeError(type(value))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--users", type=int, default=100, help="number of citizens (default 100)")
    parser.add_argument("--seed", type=int, default=int(os.environ.get("SEED", "2026")), help="random seed (default: SEED or 2026)")
    parser.add_argument("--json", metavar="FILE", help="write the generated records to FILE")
    parser.add_argument("--insert", action="store_true", help="insert into the test database")
    parser.add_argument("--database", default="smartration_test", help="test database name (must end in _test)")
    parser.add_argument("--bookings", action="store_true", help="with --insert: give each citizen one upcoming token (time slot)")
    parser.add_argument("--collections", type=float, metavar="SHARE", default=0.0,
                        help="with --insert: past collections (transactions + stock ledger) for this share of citizens, e.g. 0.5")
    args = parser.parse_args()

    try:
        people = generate(args.users, args.seed)
        validate(people)
    except SyntheticDataError as exc:
        print(exc)
        return 1
    members = sum(len(p.members) for p in people)
    print(f"Generated {len(people)} citizens ({members} family members), seed {args.seed}: validation passed.")
    print(f"  e.g. {people[0].email}, mobile {people[0].mobile}, ration card {people[0].ration_card}, Aadhaar {people[0].aadhaar_masked}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"_meta": {"isSynthetic": True, "seed": args.seed, "count": len(people)},
                       "records": [dataclasses.asdict(p) for p in people]}, f, ensure_ascii=False, indent=1, default=_json_default)
        print(f"Wrote {args.json}")

    if not args.insert:
        return 0
    if get_settings().data_mode != "synthetic":
        print("Refusing: DATA_MODE is not 'synthetic'.")
        return 1
    url = _test_url(args.database)
    print(f"Database: {safe_url(url)}")
    eng = create_engine(url, pool_pre_ping=True)
    password = os.environ.get("SYNTHETIC_USER_PASSWORD") or secrets.token_urlsafe(24)  # random = no one can log in
    start = time.perf_counter()
    try:
        with Session(eng) as db, db.begin():  # one transaction: all or nothing
            if not db.scalar(select(func.count()).select_from(RationShop)):
                print("The test database has no reference data. Run the MySQL suite or seed_database.py against it first.")
                return 1
            counts = insert(db, people, hash_password(password))
            if args.bookings:
                counts.update(book(db, people))
            if args.collections:
                counts.update(collect(db, people, args.collections))
    except IntegrityError:
        print(f"Nothing inserted: citizens for seed {args.seed} already exist in this database. Use another --seed.")
        return 1
    except SyntheticDataError as exc:
        print(exc)
        return 1
    finally:
        eng.dispose()
    print(f"Inserted in {time.perf_counter() - start:.2f} s: " + ", ".join(f"{t} {n}" for t, n in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
