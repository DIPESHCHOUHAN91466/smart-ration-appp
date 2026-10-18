"""Named locks: one holder at a time across every API process that shares the database (2026-10-17, Phase 5).

Used around short check-then-insert sections (AI-alert refreshes) that row locks cannot cover, because the row being
guarded against does not exist yet.

* MySQL: GET_LOCK / RELEASE_LOCK on a connection of its own, in autocommit mode. The lock belongs to that MySQL
  session, not to a transaction, so the request's commits and rollbacks do not release it. If the process dies or the
  connection drops, MySQL releases it, so a crash can never leave it held.
* Anything else (SQLite in the unit tests, always one process): a threading lock per name.

Hold these only for quick database work, never across a call to another service.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

log = logging.getLogger(__name__)

AI_ALERT_SYNC = "smartration:ai-alert-sync"
RULE_ALERTS = "smartration:rule-alerts"
WAIT_SECONDS = 5   # a refresh takes well under a second; past this, give up rather than tie up a request

_local: dict[str, threading.Lock] = {}
_local_guard = threading.Lock()


def _engine(db: Session) -> Engine:
    bind = db.get_bind()
    return bind if isinstance(bind, Engine) else bind.engine


@contextmanager
def named_lock(db: Session, name: str) -> Iterator[bool]:
    """Yields True while `name` is held, or False if it could not be had within WAIT_SECONDS (the caller then skips its
    work). Always released on the way out, also when the body raises."""
    engine = _engine(db)
    if engine.dialect.name != "mysql":
        with _local_guard:
            lock = _local.setdefault(name, threading.Lock())
        held = lock.acquire(timeout=WAIT_SECONDS) if WAIT_SECONDS > 0 else lock.acquire(blocking=False)
        try:
            yield held
        finally:
            if held:
                lock.release()
        return

    conn = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
    try:
        held = conn.scalar(text("SELECT GET_LOCK(:name, :wait)"), {"name": name, "wait": WAIT_SECONDS}) == 1   # 0 = timed out
    except SQLAlchemyError:
        conn.invalidate()
        conn.close()
        raise
    try:
        yield held
    finally:
        if held:
            _release(conn, name)
        conn.close()


def _release(conn: Connection, name: str) -> None:
    try:
        released = conn.scalar(text("SELECT RELEASE_LOCK(:name)"), {"name": name})
    except SQLAlchemyError:
        released = None
    if released != 1:
        # The connection dropped (MySQL has already freed the lock with it) or the lock was no longer ours. Never hand
        # this connection back to the pool: discarding it guarantees the server side lets go.
        log.warning("Named lock %s was not released cleanly; its connection is discarded.", name)
        conn.invalidate()
