"""Typed JSON request bodies with the validation messages the frontend already shows.

    body = Body(await request_json(request))
    token_id = body.integer("TokenId", required=True)
    qty = body.decimal("Quantity", minimum=Decimal("0.01"), maximum=Decimal("1000"))
    body.raise_if_invalid()

Field names are the API's PascalCase names, matched case-insensitively (camelCase from the browser works).
Every problem is collected first and reported together as HTTP 400:
    {"message": "One or more validation errors occurred.", "errors": ["TokenId: The TokenId field is required."]}
Submitted values are never echoed back.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from typing import Any, Literal, overload

from fastapi import Request

from app.core.validation import ValidationFailed, phone, string_length


async def request_json(request: Request) -> Any:
    try:
        return json.loads(await request.body() or b"null")
    except ValueError:
        raise ValidationFailed(["$: The request body is not valid JSON."]) from None


def _fmt(value: Decimal) -> str:
    return format(value.normalize(), "f")


class Body:
    def __init__(self, data: Any):
        if not isinstance(data, dict):
            raise ValidationFailed(["request: The request field is required."])
        self._values = {str(k).lower(): v for k, v in data.items()}
        self.errors: list[str] = []

    def _get(self, field: str) -> Any:
        return self._values.get(field.lower())

    def raw(self, field: str) -> Any:
        """The submitted value as-is (None when missing), for types parsed by the caller."""
        return self._get(field)

    def _json_error(self, field: str, type_name: str) -> None:
        self.errors.append(f"$.{field[0].lower()}{field[1:]}: The JSON value could not be converted to {type_name}.")

    # A `required=True` getter always returns a value (a placeholder when invalid); the error is
    # recorded, and callers use the value only after raise_if_invalid(), so the placeholder is never used.
    @overload
    def integer(self, field: str, *, required: Literal[True], minimum: int | None = None, maximum: int | None = None) -> int: ...
    @overload
    def integer(self, field: str, *, required: bool = False, minimum: int | None = None, maximum: int | None = None) -> int | None: ...

    def integer(self, field: str, *, required: bool = False, minimum: int | None = None, maximum: int | None = None) -> int | None:
        raw = self._get(field)
        if raw is None:
            if required:
                self.errors.append(f"{field}: The {field} field is required.")
                return 0
            return None
        if isinstance(raw, bool) or not isinstance(raw, int):
            self._json_error(field, "System.Int32")
            return 0 if required else None
        if (minimum is not None and raw < minimum) or (maximum is not None and raw > maximum):
            self.errors.append(f"{field}: The field {field} must be between {minimum} and {maximum}.")
        return raw

    def decimal(self, field: str, *, required: bool = False, minimum: Decimal | None = None,
                maximum: Decimal | None = None) -> Decimal:
        """Missing -> 0 (like a .NET decimal property); an invalid value records an error and returns 0."""
        raw = self._get(field)
        if raw is None:
            if required:
                self.errors.append(f"{field}: The {field} field is required.")
            return Decimal(0)
        if isinstance(raw, bool) or not isinstance(raw, int | float):
            self._json_error(field, "System.Decimal")
            return Decimal(0)
        try:
            value = Decimal(str(raw))
        except InvalidOperation:
            self._json_error(field, "System.Decimal")
            return Decimal(0)
        if (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
            low = _fmt(minimum) if minimum is not None else "0"
            high = _fmt(maximum) if maximum is not None else "1.7976931348623157E+308"
            self.errors.append(f"{field}: The field {field} must be between {low} and {high}.")
        return value

    @overload
    def string(self, field: str, *, required: Literal[True], max_length: int | None = None, min_length: int = 0,
               is_phone: bool = False) -> str: ...
    @overload
    def string(self, field: str, *, required: bool = False, max_length: int | None = None, min_length: int = 0,
               is_phone: bool = False) -> str | None: ...

    def string(self, field: str, *, required: bool = False, max_length: int | None = None, min_length: int = 0,
               is_phone: bool = False) -> str | None:
        raw = self._get(field)
        if raw is not None and not isinstance(raw, str):
            self._json_error(field, "System.String")
            return "" if required else None
        if raw is None or raw.strip() == "":
            if required:
                self.errors.append(f"{field}: The {field} field is required.")
                return raw or ""
        if raw is None:
            return None
        if max_length is not None:
            message = string_length(max_length, min_length)(field, raw)
            if message:
                self.errors.append(f"{field}: {message}")
        if is_phone and raw.strip():
            message = phone(field, raw)
            if message:
                self.errors.append(f"{field}: {message}")
        return raw

    def objects(self, field: str, *, min_items: int = 0, min_message: str | None = None) -> list[dict]:
        raw = self._get(field)
        if raw is None:
            raw = []
        if not isinstance(raw, list) or any(not isinstance(item, dict) for item in raw):
            self._json_error(field, "System.Collections.Generic.List")
            return []
        if len(raw) < min_items:
            self.errors.append(f"{field}: {min_message or f'The field {field} must be a string or array type with a minimum length of {min_items}.'}")
        return raw

    def integers(self, field: str, *, min_items: int = 0) -> list[int]:
        raw = self._get(field)
        if raw is None:
            raw = []
        if not isinstance(raw, list) or any(isinstance(v, bool) or not isinstance(v, int) for v in raw):
            self._json_error(field, "System.Collections.Generic.List")
            return []
        if len(raw) < min_items:
            self.errors.append(f"{field}: The field {field} must be a string or array type with a minimum length of {min_items}.")
        return raw

    def raise_if_invalid(self) -> None:
        if self.errors:
            raise ValidationFailed(self.errors)


def nested(items: Sequence[dict], prefix: str) -> list[NestedBody]:
    """Bodies for list elements; their errors are reported as e.g. 'Items[0].Quantity: ...'."""
    return [NestedBody(item, f"{prefix}[{i}].") for i, item in enumerate(items)]


class NestedBody(Body):
    def __init__(self, data: dict, prefix: str):
        super().__init__(data)
        self.prefix = prefix

    def raise_if_invalid(self) -> None:  # pragma: no cover - nested bodies report through the parent
        raise NotImplementedError

    @property
    def prefixed_errors(self) -> list[str]:
        return [self.prefix + e for e in self.errors]
