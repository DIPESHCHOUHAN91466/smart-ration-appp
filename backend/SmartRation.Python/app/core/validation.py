"""Request validation that reproduces ASP.NET Core DataAnnotations behaviour.

The frontend receives the C# API's validation messages today, e.g.
    "Email: The Email field is not a valid e-mail address."
so migrated endpoints must produce the same text. Like MVC, every rule on a
field is evaluated independently (an empty email yields both "required" and
"not a valid e-mail address"). Failure -> HTTP 400 envelope, no errorCode.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from app.core.errors import ApiError

Rule = Callable[[str, object], str | None]


class ValidationFailed(ApiError):
    status_code = 400

    def __init__(self, errors: list[str]):
        super().__init__("One or more validation errors occurred.")
        self.errors = errors


def required(field: str, value: object) -> str | None:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return f"The {field} field is required."
    return None


def email_address(field: str, value: object) -> str | None:
    # .NET EmailAddressAttribute: null passes; otherwise exactly one '@',
    # not first, not last, and no line breaks.
    if value is None:
        return None
    text = str(value)
    at = text.find("@")
    ok = at > 0 and at == text.rfind("@") and at != len(text) - 1 and "\r" not in text and "\n" not in text
    return None if ok else f"The {field} field is not a valid e-mail address."


_EXTENSION = re.compile(r"(\s*(ext|ext\.|x)\s*\d+)$", re.IGNORECASE)


def phone(field: str, value: object) -> str | None:
    # .NET PhoneAttribute: '+' ignored, optional trailing extension, then only
    # digits / whitespace / - . ( ) with at least one digit.
    if value is None:
        return None
    text = _EXTENSION.sub("", str(value).replace("+", "").rstrip())
    ok = any(c.isdigit() for c in text) and all(c.isdigit() or c.isspace() or c in "-.()" for c in text)
    return None if ok else f"The {field} field is not a valid phone number."


def string_length(maximum: int, minimum: int = 0) -> Rule:
    def rule(field: str, value: object) -> str | None:
        if value is None:
            return None
        length = len(str(value))
        if minimum <= length <= maximum:
            return None
        if minimum:
            return f"The field {field} must be a string with a minimum length of {minimum} and a maximum length of {maximum}."
        return f"The field {field} must be a string with a maximum length of {maximum}."
    return rule


def validate(body: dict | None, schema: dict[str, list[Rule]]) -> dict[str, str]:
    """Validate a JSON object against {FieldName: [rules]} (C# property names,
    matched case-insensitively like MVC model binding). Returns clean strings."""
    if not isinstance(body, dict):
        raise ValidationFailed(["request: The request field is required."])

    lowered = {str(k).lower(): v for k, v in body.items()}
    values: dict[str, str] = {}
    errors: list[str] = []
    for field, rules in schema.items():
        raw = lowered.get(field.lower())
        if raw is not None and not isinstance(raw, str):
            errors.append(f"$.{field[0].lower()}{field[1:]}: The JSON value could not be converted to System.String.")
            continue
        value = "" if raw is None else raw  # C# non-nullable string properties default to ""
        for rule in rules:
            message = rule(field, value)
            if message:
                errors.append(f"{field}: {message}")
        values[field] = value
    if errors:
        raise ValidationFailed(errors)
    return values
