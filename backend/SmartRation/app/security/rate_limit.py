"""Fixed-window, per-client-IP rate limiting (the C# AddRateLimiter policies).

In-memory and per process — the same scope as the C# limiter. Run a shared
store (e.g. Redis) before scaling to several Python processes.

    @router.post("/login", dependencies=[Depends(rate_limit("auth", lambda s: s.auth_rate_limit_per_minute))])
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

from fastapi import Request

from app.config.settings import Settings
from app.core.errors import ApiError

WINDOW_SECONDS = 60
clock = time.time   # replaceable in tests, so a burst of requests can't straddle a window boundary


class TooManyRequests(ApiError):
    status_code = 429


class FixedWindowLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._windows: dict[tuple[str, str], tuple[int, int]] = {}  # (policy, ip) -> (window, count)

    def allow(self, policy: str, key: str, limit: int) -> bool:
        window = int(clock() // WINDOW_SECONDS)
        with self._lock:
            start, count = self._windows.get((policy, key), (window, 0))
            if start != window:
                start, count = window, 0
            if count >= limit:
                return False
            self._windows[(policy, key)] = (start, count + 1)
            if len(self._windows) > 50_000:  # drop stale windows
                self._windows = {k: v for k, v in self._windows.items() if v[0] == window}
            return True


def rate_limit(policy: str, limit_of: Callable[[Settings], int]):
    def dependency(request: Request) -> None:
        limiter: FixedWindowLimiter = request.app.state.rate_limiter
        ip = request.client.host if request.client else "unknown"
        if not limiter.allow(policy, ip, limit_of(request.app.state.settings)):
            raise TooManyRequests("Too many requests. Please wait a moment and try again.")

    return dependency
