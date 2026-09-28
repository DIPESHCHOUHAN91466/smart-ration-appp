"""Masking for personal data that may appear in audit rows, logs or API responses.

Same output as the C# API (MaskingUtil, AuthService.MaskEmail), so both backends write identical audit details.
"""

from __future__ import annotations


def mask_email(email: str) -> str:
    """'rahul@example.com' -> 'r***@example.com'; anything without a local part -> '***'."""
    at = email.find("@")
    return "***" if at <= 0 else f"{email[0]}***{email[at:]}"


def mask_mobile(mobile: str) -> str:
    """'9000000001' -> '******0001'; shorter than 4 characters -> '****'."""
    return "****" if not mobile or len(mobile) < 4 else "******" + mobile[-4:]


def mask_aadhaar(value: str) -> str:
    """Any Aadhaar-like number -> 'XXXX-XXXX-1234' (last four digits only); fewer than 4 digits -> 'XXXX-XXXX-XXXX'."""
    digits = "".join(ch for ch in value if ch.isdigit())
    return f"XXXX-XXXX-{digits[-4:]}" if len(digits) >= 4 else "XXXX-XXXX-XXXX"
