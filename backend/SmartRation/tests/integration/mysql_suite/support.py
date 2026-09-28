"""Shared pieces of the MySQL suite (imported by conftest and the test modules)."""

from __future__ import annotations

import time
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.database import session as database

KEY = "mysql-suite-signing-key-0123456789abcdef-0123456789"


def new_session() -> Session:
    return database.get_session_factory()()


_REPORT: list[tuple[str, float, str]] = []


def record_fixture() -> Callable[[str, float, str], None]:
    def add(name: str, seconds: float, note: str = "") -> None:
        _REPORT.append((name, seconds, note))
    return add


def stats(samples: list[float]) -> str:
    """'n=1000 total 812.3 ms | avg 0.81 / min 0.52 / median 0.74 / max 6.10 ms' for the report."""
    ordered = sorted(samples)
    n = len(ordered)
    median = ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2
    ms = [x * 1000 for x in (sum(ordered), sum(ordered) / n, ordered[0], median, ordered[-1])]
    return f"n={n} total {ms[0]:.1f} ms | avg {ms[1]:.2f} / min {ms[2]:.2f} / median {ms[3]:.2f} / max {ms[4]:.2f} ms"


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.seconds = time.perf_counter() - self.start
