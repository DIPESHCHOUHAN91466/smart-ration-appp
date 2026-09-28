"""app.workers.cleanup — deletes only long-expired refresh tokens, through the app's own database settings."""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import select

import app.database.models  # noqa: F401  (register tables)
from app.database import connection as database
from app.database.base import Base
from app.database.models import AuditLog, RefreshToken, User
from app.utils.time import utc_now
from app.workers import cleanup


@pytest.fixture
def seeded(tmp_path):
    database.configure_database(f"sqlite:///{(tmp_path / 'worker.db').as_posix()}")
    Base.metadata.create_all(database.get_engine())
    now = utc_now()
    with database.get_session_factory()() as db:
        db.add(User(Id=1, FullName="U", Email="u@example.com", MobileNumber="9000000001", PasswordHash="x", Role=1, IsActive=True, CreatedAt=now))
        db.flush()
        db.add_all([
            RefreshToken(UserId=1, TokenHash="LIVE", ExpiresAt=now + timedelta(days=7), CreatedAt=now),
            RefreshToken(UserId=1, TokenHash="REVOKED-NOT-EXPIRED", ExpiresAt=now + timedelta(days=3), CreatedAt=now, RevokedAt=now),
            RefreshToken(UserId=1, TokenHash="EXPIRED-10-DAYS", ExpiresAt=now - timedelta(days=10), CreatedAt=now - timedelta(days=17)),
            RefreshToken(UserId=1, TokenHash="EXPIRED-60-DAYS", ExpiresAt=now - timedelta(days=60), CreatedAt=now - timedelta(days=67)),
            AuditLog(UserId=1, Action="LOGIN", EntityName="User", Result="SUCCESS", CreatedAt=now - timedelta(days=400)),
        ])
        db.commit()
    yield
    database.get_engine().dispose()


def hashes() -> list[str]:
    with database.get_session_factory()() as db:
        return sorted(db.scalars(select(RefreshToken.TokenHash)).all())


def test_dry_run_counts_and_deletes_nothing(seeded, capsys):
    assert cleanup.main(["--dry-run"]) == 0
    assert "would delete 1" in capsys.readouterr().out
    assert len(hashes()) == 4


def test_default_run_deletes_only_tokens_expired_over_30_days_ago(seeded, capsys):
    assert cleanup.main([]) == 0
    assert "deleted 1" in capsys.readouterr().out
    assert hashes() == ["EXPIRED-10-DAYS", "LIVE", "REVOKED-NOT-EXPIRED"]


def test_retention_zero_deletes_every_expired_token_but_keeps_usable_and_revoked_ones(seeded):
    assert cleanup.main(["--retention-days", "0"]) == 0
    assert hashes() == ["LIVE", "REVOKED-NOT-EXPIRED"]


def test_audit_logs_are_never_touched(seeded):
    cleanup.main(["--retention-days", "0"])
    with database.get_session_factory()() as db:
        assert db.scalar(select(AuditLog.Action)) == "LOGIN"


def test_negative_retention_is_rejected(seeded):
    with pytest.raises(SystemExit):
        cleanup.main(["--retention-days", "-1"])


def test_unreachable_database_exits_1_without_details(tmp_path, capsys):
    database.configure_database(f"sqlite:///{(tmp_path / 'missing-dir' / 'nope.db').as_posix()}")
    try:
        assert cleanup.main([]) == 1
        err = capsys.readouterr().err
        assert "database error" in err and "missing-dir" not in err
    finally:
        database.get_engine().dispose()
