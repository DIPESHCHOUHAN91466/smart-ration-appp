"""Performance: 100 records one at a time vs. as a batch; pooled vs. fresh connections.

Timings print in the "MySQL performance" section at the end of the run. The assertions are
deliberately generous (a slow laptop must pass); what they pin down is the *shape*: batching and
pooling must win clearly, and round trips must drop from ~hundreds to a handful.
"""

from __future__ import annotations

import tracemalloc

from sqlalchemy import create_engine, delete, func, insert, select, text
from sqlalchemy.pool import NullPool

from app.models import User
from app.models.enums import UserRole
from app.utils.time import utc_now
from mysql_suite.sample_data import people
from mysql_suite.support import Timer


def rows(prefix: str, password_hash: str) -> list[dict]:
    return [dict(FullName=p.full_name, Email=p.email, MobileNumber=p.mobile, PasswordHash=password_hash,
                 Role=int(UserRole.RuralUser), IsActive=True, CreatedAt=utc_now()) for p in people(prefix)]


def questions(conn) -> int:
    """Statements the server has received on this connection (round trips)."""
    return int(conn.execute(text("SHOW SESSION STATUS LIKE 'Questions'")).one()[1])


def test_insert_individual_vs_batch(db, engine, password_hash, record):
    data_one, data_batch = rows("perf1", password_hash), rows("perf2", password_hash)

    with engine.connect() as conn:
        q0 = questions(conn)
        with Timer() as individual:
            for row in data_one:                      # 100 statements + 100 commits
                conn.execute(insert(User).values(**row))
                conn.commit()
        q1 = questions(conn)
        with Timer() as batch:                        # 1 multi-row statement + 1 commit
            conn.execute(insert(User), data_batch)
            conn.commit()
        q2 = questions(conn)

    individual_trips, batch_trips = q1 - q0 - 1, q2 - q1 - 1   # minus the SHOW STATUS itself
    record("insert 100 users, one transaction each", individual.seconds, f"{individual_trips} round trips")
    record("insert 100 users, one batch transaction", batch.seconds, f"{batch_trips} round trips")

    assert db.scalar(select(func.count()).select_from(User)) == 200
    assert individual.seconds < 15 and batch.seconds < 3
    assert batch.seconds < individual.seconds
    assert individual_trips >= 200 and batch_trips <= 10


def test_read_individual_vs_single_query(db, engine, password_hash, record):
    data = rows("perf3", password_hash)
    with engine.begin() as conn:
        conn.execute(insert(User), data)
    emails = [r["Email"] for r in data]

    with engine.connect() as conn:
        with Timer() as individual:
            one_by_one = [conn.execute(select(User.Id).where(User.Email == e)).scalar_one() for e in emails]
        with Timer() as single:
            together = conn.execute(select(User.Id).where(User.Email.in_(emails))).scalars().all()
        with Timer() as full_scan_free:
            plan = conn.execute(text("EXPLAIN SELECT Id FROM Users WHERE Email = :e"), {"e": emails[0]}).mappings().one()

    record("read 100 users, 100 queries (indexed)", individual.seconds)
    record("read 100 users, one IN (...) query", single.seconds)
    assert sorted(one_by_one) == sorted(together) and len(together) == 100
    assert single.seconds < individual.seconds
    assert plan["key"] == "IX_Users_Email"           # lookups use the unique index, not a table scan
    assert full_scan_free.seconds < 1


def test_update_and_delete_batch(db, engine, password_hash, record):
    with engine.begin() as conn:
        conn.execute(insert(User), rows("perf4", password_hash))
    with Timer() as upd, engine.begin() as conn:
        changed = conn.execute(User.__table__.update().where(User.Email.like("perf4.%")).values(IsActive=False)).rowcount
    with Timer() as dele, engine.begin() as conn:
        removed = conn.execute(delete(User).where(User.Email.like("perf4.%"))).rowcount
    record("update 100 users, one statement", upd.seconds)
    record("delete 100 users, one statement", dele.seconds)
    assert changed == removed == 100


def test_pooled_vs_new_connection_per_query(engine, test_url, record):
    unpooled = create_engine(test_url, poolclass=NullPool)
    with Timer() as fresh:
        for _ in range(100):
            with unpooled.connect() as conn:
                conn.execute(text("SELECT 1"))
    unpooled.dispose()
    with Timer() as pooled:
        for _ in range(100):
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
    record("100 queries, new connection each (no pool)", fresh.seconds)
    record("100 queries, pooled connection", pooled.seconds, f"{fresh.seconds / max(pooled.seconds, 1e-6):.0f}x faster")
    assert pooled.seconds < fresh.seconds


def test_memory_for_100_records_is_small(db, engine, password_hash, record):
    with engine.begin() as conn:
        conn.execute(insert(User), rows("perf5", password_hash))
    tracemalloc.start()
    loaded = db.scalars(select(User)).all()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    record("load 100 users as ORM objects", 0.0, f"peak {peak / 1024:.0f} KiB Python memory")
    assert len(loaded) == 100
    assert peak < 10 * 1024 * 1024
