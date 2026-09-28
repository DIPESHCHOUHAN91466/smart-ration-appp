"""Latency budgets for the hot paths, measured in-process so they run in every test run.

These catch accidental slowdowns (a query in a loop, a knowledge base reloaded per message), not
capacity: budgets are several times the measured values so a busy CI machine does not fail them.
Capacity under concurrent users (10 / 100 / 1,000) is measured separately against a running
stack with scripts/load_test.py — see docs/testing/LOAD_TESTING.md.
"""

from __future__ import annotations

import statistics
import time
from collections.abc import Callable

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401  (register tables)
from app.ai.chatbot.engine import Assistant
from app.ai.chatbot.knowledge_base import load
from app.database.base import Base
from app.models import User
from app.repositories import users
from app.utils.time import utc_now

QUESTIONS = [
    ("How do I book a ration slot?", "en"),
    ("What documents do I need for a ration card?", "en"),
    ("राशन कार्ड के लिए कौन से दस्तावेज़ चाहिए?", "hi"),
    ("रेशन दुकान कधी उघडते?", "mr"),
    ("my QR code is not working", "en"),
]


def p95_ms(action: Callable[[], object], runs: int) -> float:
    action()  # warm-up (imports, caches)
    samples = []
    for _ in range(runs):
        started = time.perf_counter()
        action()
        samples.append((time.perf_counter() - started) * 1000)
    return statistics.quantiles(samples, n=20)[18]


def test_chatbot_reply_p95_under_50_ms():
    bot = Assistant(load())
    cycle = iter(QUESTIONS * 100)
    p95 = p95_ms(lambda: bot.reply(*next(cycle)), runs=300)
    assert p95 < 50, f"chatbot p95 {p95:.1f} ms"


def test_liveness_endpoint_p95_under_25_ms(make_client):
    client = make_client(lambda r: None)
    p95 = p95_ms(lambda: client.get("/health/live"), runs=200)
    assert p95 < 25, f"/health/live p95 {p95:.1f} ms"


@pytest.fixture
def db_with_users(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'perf.db').as_posix()}")
    Base.metadata.create_all(engine)
    now = utc_now()
    with sessionmaker(bind=engine)() as db:
        db.add_all(User(FullName=f"User {i}", Email=f"user{i}@example.com", MobileNumber=f"9{i:09d}", PasswordHash="x",
                        Role=1, IsActive=True, CreatedAt=now) for i in range(5000))
        db.commit()
        yield db
    engine.dispose()


def test_user_lookup_by_email_uses_the_index_p95_under_5_ms(db_with_users):
    emails = iter([f"user{i}@example.com" for i in range(0, 5000, 17)] * 3)
    p95 = p95_ms(lambda: users.by_email(db_with_users, next(emails)), runs=250)
    assert p95 < 5, f"user lookup p95 {p95:.2f} ms over 5,000 users"
