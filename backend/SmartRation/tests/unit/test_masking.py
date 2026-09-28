"""app.utils.masking — the only way personal data may appear in audit rows and logs."""

from __future__ import annotations

import pytest

from app.utils.masking import mask_aadhaar, mask_email, mask_mobile


@pytest.mark.parametrize(("email", "masked"), [
    ("rahul@example.com", "r***@example.com"),
    ("a@b.in", "a***@b.in"),
    ("@example.com", "***"),
    ("no-at-sign", "***"),
    ("", "***"),
])
def test_mask_email(email, masked):
    assert mask_email(email) == masked


@pytest.mark.parametrize(("mobile", "masked"), [
    ("9000000001", "******0001"),
    ("1234", "******1234"),
    ("123", "****"),
    ("", "****"),
])
def test_mask_mobile_matches_the_csharp_masking_util(mobile, masked):
    assert mask_mobile(mobile) == masked


@pytest.mark.parametrize(("value", "masked"), [
    ("999900001234", "XXXX-XXXX-1234"),
    ("9999 0000 5678", "XXXX-XXXX-5678"),
    ("XXXX-XXXX-4321", "XXXX-XXXX-4321"),
    ("12", "XXXX-XXXX-XXXX"),
    ("", "XXXX-XXXX-XXXX"),
])
def test_mask_aadhaar_keeps_only_the_last_four_digits(value, masked):
    assert mask_aadhaar(value) == masked


def test_masked_values_never_contain_the_hidden_part():
    assert "90000000" not in mask_mobile("9000000001")
    assert "99990000" not in mask_aadhaar("999900001234").replace("-", "")
    assert "ahul" not in mask_email("rahul@example.com")
