"""Users table queries."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import User


def email_taken(db: Session, email: str) -> bool:
    return db.scalar(select(User.Id).where(User.Email == email)) is not None


def mobile_taken(db: Session, mobile: str) -> bool:
    return db.scalar(select(User.Id).where(User.MobileNumber == mobile)) is not None


def by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.Email == email))


def by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def add(db: Session, user: User) -> User:
    """Adds and flushes, so user.Id is set; the caller commits."""
    db.add(user)
    db.flush()
    return user
