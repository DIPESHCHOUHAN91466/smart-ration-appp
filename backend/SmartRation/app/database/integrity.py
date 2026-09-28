"""Data-integrity checks: the read-only SQL files in <repo>/database/queries, run against a database.

Each file holds one SELECT that returns the rows breaking one rule (first column `id`), with a header:

    -- check: overbooked_time_slots
    -- severity: error | warning
    -- why: the rule and where the application enforces it

Only SELECT / WITH statements are accepted, and they run in a transaction that is rolled back, so a
check can never change data. Results carry ids and counts only, never personal values.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

# <repo>/database/queries; INTEGRITY_QUERIES_DIR overrides it (the Docker image copies them to /app).
QUERIES_DIR = Path(os.environ.get("INTEGRITY_QUERIES_DIR") or Path(__file__).resolve().parents[4] / "database" / "queries")
SEVERITIES = ("error", "warning")
_HEADER = re.compile(r"^--\s*(check|severity|why):\s*(.*)$")


class InvalidCheck(ValueError):
    pass


@dataclass(frozen=True)
class Check:
    name: str
    severity: str
    why: str
    sql: str
    source: str


@dataclass
class CheckResult:
    check: Check
    violations: int
    sample_ids: list[str] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        return self.violations > 0


def parse_check(path: Path) -> Check:
    meta: dict[str, str] = {}
    body: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _HEADER.match(line.strip())
        if match:
            key, value = match.groups()
            meta[key] = (meta.get(key, "") + " " + value).strip() if key == "why" else value.strip()
        elif line.strip().startswith("--"):
            if "why" in meta and not body:  # continuation of the "why" comment
                meta["why"] += " " + line.strip().lstrip("-").strip()
        elif line.strip():
            body.append(line)
    sql = "\n".join(body).strip().rstrip(";")
    if not meta.get("check") or meta.get("severity") not in SEVERITIES:
        raise InvalidCheck(f"{path.name}: needs '-- check: <name>' and '-- severity: error|warning'")
    if not re.match(r"(?is)^(select|with)\b", sql) or ";" in sql:
        raise InvalidCheck(f"{path.name}: must be a single SELECT (or WITH ... SELECT) statement")
    return Check(meta["check"], meta["severity"], meta.get("why", ""), sql, path.name)


def load_checks(directory: Path = QUERIES_DIR) -> list[Check]:
    files = sorted(directory.glob("*.sql"))
    if not files:
        raise InvalidCheck(f"no *.sql checks in {directory}")
    checks = [parse_check(p) for p in files]
    names = [c.name for c in checks]
    if len(names) != len(set(names)):
        raise InvalidCheck("duplicate check names")
    return checks


def run_checks(engine: Engine, checks: list[Check], sample_size: int = 5) -> list[CheckResult]:
    results = []
    with engine.connect() as conn:
        with conn.begin() as tx:
            try:
                for check in checks:
                    rows = conn.execute(text(check.sql)).all()
                    results.append(CheckResult(check, len(rows), [str(r[0]) for r in rows[:sample_size]]))
            finally:
                tx.rollback()  # read-only by construction; never commit anything
    return results
