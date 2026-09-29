"""Client for the OPTIONAL Python AI analytics service (ai/, `/v1/*`, authenticated with X-Api-Key).

It never raises for transport problems: an unavailable AI service is a normal, expected state, and every
caller has a rule-based fallback or shows "unavailable". The API key is sent only as a header and never
logged.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

log = logging.getLogger("smartration.ai")


@dataclass(frozen=True)
class AiResult:
    available: bool
    data: Any = None
    error_code: str | None = None
    message: str | None = None


class AiClient:
    def __init__(self, base_url: str, api_key: str, timeout: float, transport: httpx.BaseTransport | None = None):
        self._api_key = api_key
        self._http = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout, transport=transport) if base_url else None

    @property
    def is_configured(self) -> bool:
        return self._http is not None and bool(self._api_key)

    def get(self, path: str, query: dict[str, str | None]) -> AiResult:
        return self._send("GET", path, params={k: v for k, v in query.items() if v})

    def post(self, path: str, body: dict) -> AiResult:
        return self._send("POST", path, json=body)

    def _send(self, method: str, path: str, **kwargs: Any) -> AiResult:
        if not self.is_configured or self._http is None:
            return AiResult(False, None, "AI_NOT_CONFIGURED", "The AI analytics service is not configured.")
        try:
            response = self._http.request(method, path, headers={"X-Api-Key": self._api_key}, **kwargs)
        except httpx.HTTPError as exc:
            log.warning("AI service %s unreachable: %s", path, type(exc).__name__)
            return AiResult(False, None, "AI_UNAVAILABLE", "The AI analytics service is temporarily unavailable.")
        try:
            body = response.json()
        except ValueError:
            # Proxy error page, truncated body, etc. — malformed, not data.
            log.warning("AI service %s returned a non-JSON body (%s)", path, response.status_code)
            return AiResult(False, None, "AI_MALFORMED_RESPONSE", "The AI service returned an unreadable response.")
        if response.is_success and isinstance(body, dict) and "data" in body:
            return AiResult(True, body["data"])
        code = body.get("error_code") if isinstance(body, dict) else None
        message = body.get("message") if isinstance(body, dict) else None
        log.warning("AI service %s returned %s %s", path, response.status_code, code or "AI_MALFORMED_RESPONSE")
        return AiResult(False, None, code or "AI_MALFORMED_RESPONSE", message or "The AI service returned an unexpected response.")

    def close(self) -> None:
        if self._http is not None:
            self._http.close()
