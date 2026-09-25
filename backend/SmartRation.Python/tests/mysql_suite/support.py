"""Shared pieces of the MySQL suite (imported by conftest and the test modules)."""

from __future__ import annotations

import time
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.db import database

KEY = "mysql-suite-signing-key-0123456789abcdef-0123456789"


def new_session() -> Session:
    return database.get_session_factory()()


_REPORT: list[tuple[str, float, str]] = []


def record_fixture() -> Callable[[str, float, str], None]:
    def add(name: str, seconds: float, note: str = "") -> None:
        _REPORT.append((name, seconds, note))
    return add


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.seconds = time.perf_counter() - self.start
