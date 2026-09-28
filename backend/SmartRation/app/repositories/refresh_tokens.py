"""RefreshTokens table queries. Only SHA-256 hashes are stored; raw tokens never reach this module."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import RefreshToken


def add(db: Session, user_id: int, token_hash: str, expires_at: datetime, created_at: datetime) -> None:
    db.add(RefreshToken(UserId=user_id, TokenHash=token_hash, ExpiresAt=expires_at, CreatedAt=created_at))


def by_hash(db: Session, token_hash: str, *, for_update: bool = False) -> RefreshToken | None:
    """for_update=True locks the row (SELECT ... FOR UPDATE) so two concurrent refreshes can't both rotate it."""
    query = select(RefreshToken).where(RefreshToken.TokenHash == token_hash)
    return db.scalar(query.with_for_update() if for_update else query)


def delete_expired_before(db: Session, cutoff: datetime) -> int:
    """Deletes tokens that expired before `cutoff` (unusable by either backend); returns the count.
    Revoked tokens that have not expired yet are kept."""
    result = db.execute(delete(RefreshToken).where(RefreshToken.ExpiresAt < cutoff))
    return int(getattr(result, "rowcount", 0) or 0)


def count_expired_before(db: Session, cutoff: datetime) -> int:
    return int(db.scalar(select(func.count()).select_from(RefreshToken).where(RefreshToken.ExpiresAt < cutoff)) or 0)
