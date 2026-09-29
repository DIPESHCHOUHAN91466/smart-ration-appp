"""Loading a row that must exist (e.g. the slot a token points to — guaranteed by a foreign key)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import NotFound


def require[T](db: Session, model: type[T], key: Any, message: str = "Record not found.") -> T:
    row = db.get(model, key)
    if row is None:
        raise NotFound(message)
    return row
