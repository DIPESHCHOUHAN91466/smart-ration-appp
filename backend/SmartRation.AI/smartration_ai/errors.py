"""Structured, API-safe errors. Messages never include stack traces or data values."""

from __future__ import annotations


class AIServiceError(Exception):
    """An expected failure with a stable machine-readable code."""

    def __init__(self, error_code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code


class DatabaseUnavailable(AIServiceError):
    def __init__(self) -> None:
        super().__init__("DATABASE_UNAVAILABLE", "The database is temporarily unavailable. Please retry.", 503)


class InvalidInput(AIServiceError):
    def __init__(self, message: str) -> None:
        super().__init__("INVALID_INPUT", message, 422)
