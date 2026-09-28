"""Housekeeping job: delete refresh tokens that expired more than N days ago.

Every login and refresh adds a RefreshTokens row, and nothing removed them, so the table only grew.
An expired token can never be used again by either backend, so deleting it changes no behaviour;
revoked tokens that have not expired yet are kept. Audit logs are never deleted.

Run once (from backend/SmartRation):
    python -m app.workers.cleanup                   # delete tokens expired > 30 days ago
    python -m app.workers.cleanup --dry-run         # only count them
    python -m app.workers.cleanup --every-hours 24  # keep running, once a day (a simple worker process)

Uses DATABASE_URL like the API. Exit code 0 on success, 1 if the database could not be reached.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.core.logging import configure_logging
from app.database.session import get_session_factory
from app.repositories import refresh_tokens
from app.utils.time import utc_now

log = logging.getLogger("smartration.worker.cleanup")

DEFAULT_RETENTION_DAYS = 30


@dataclass(frozen=True)
class CleanupResult:
    expired_refresh_tokens: int
    dry_run: bool


def purge_expired_refresh_tokens(db: Session, retention_days: int = DEFAULT_RETENTION_DAYS, *, dry_run: bool = False) -> CleanupResult:
    """Deletes (or with dry_run only counts) tokens whose ExpiresAt is older than `retention_days`; commits."""
    if retention_days < 0:
        raise ValueError("retention_days must be 0 or more")
    cutoff = utc_now() - timedelta(days=retention_days)
    if dry_run:
        return CleanupResult(refresh_tokens.count_expired_before(db, cutoff), dry_run=True)
    deleted = refresh_tokens.delete_expired_before(db, cutoff)
    db.commit()
    return CleanupResult(deleted, dry_run=False)


def run_once(retention_days: int, dry_run: bool) -> CleanupResult:
    with get_session_factory()() as db:
        result = purge_expired_refresh_tokens(db, retention_days, dry_run=dry_run)
    verb = "would delete" if result.dry_run else "deleted"
    log.info("cleanup finished", extra={"fields": {"expired_refresh_tokens": result.expired_refresh_tokens, "dry_run": result.dry_run}})
    print(f"Refresh tokens expired more than {retention_days} days ago: {verb} {result.expired_refresh_tokens}.")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--retention-days", type=int, default=DEFAULT_RETENTION_DAYS, help="keep tokens that expired fewer days ago (default 30)")
    parser.add_argument("--dry-run", action="store_true", help="count only, delete nothing")
    parser.add_argument("--every-hours", type=float, default=None, help="repeat forever with this interval instead of running once")
    args = parser.parse_args(argv)
    if args.retention_days < 0:
        parser.error("--retention-days must be 0 or more")

    configure_logging(get_settings().log_level)
    while True:
        try:
            run_once(args.retention_days, args.dry_run)
        except SQLAlchemyError as exc:
            log.error("cleanup failed: database error", extra={"fields": {"error": type(exc).__name__}})
            print(f"Cleanup failed: database error ({type(exc).__name__}).", file=sys.stderr)
            if args.every_hours is None:
                return 1
        if args.every_hours is None:
            return 0
        time.sleep(args.every_hours * 3600)


if __name__ == "__main__":
    sys.exit(main())
