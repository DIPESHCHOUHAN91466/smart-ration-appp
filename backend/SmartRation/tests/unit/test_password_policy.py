"""New-password policy (N9): length over composition, no common, personal or repetitive passwords."""

from __future__ import annotations

import pytest

from app.security import password_policy as policy


@pytest.mark.parametrize("good", ["Kite-River-Lamp-42", "monsoon tea at five", "मेरा राशन कार्ड 2026", "x7#Qm!rT9@wLp"])
def test_long_unpredictable_passwords_are_accepted(good):
    assert policy.problems(good, email="sunita@example.com", mobile="9000000001", full_name="Sunita More") == []


def test_length_limits():
    assert policy.problems("Short-Pw-1") == [policy.TOO_SHORT]                 # 10 characters
    assert policy.problems("a" * 3 + "Long-Enough!") == []                     # exactly 15, fine
    assert policy.problems("Kite-River-" * 10) == [policy.TOO_LONG]            # 110 characters


@pytest.mark.parametrize("common", ["password1234", "Password1234", "qwertyuiop123", "123456789012", "password1234!"])
def test_common_passwords_are_refused_case_insensitively(common):
    assert policy.problems(common) in ([policy.TOO_COMMON], [policy.TOO_REPETITIVE])


def test_the_common_list_ships_with_the_code_and_has_only_12_plus_entries():
    common = policy._common()
    assert len(common) > 1000 and all(len(p) >= 12 for p in common)


@pytest.mark.parametrize("personal, found, source", [
    ("sunita.more.2026", "sunita.more", "your email"),
    ("my-9000000001-pin", "9000000001", "your mobile number"),
    ("SmartRation-2026!", "smartration", "the service's name"),
    ("ration mitra rocks", "rationmitra", "the service's name"),
    ("x-sunita-x-2026-blue", "sunita", "your name"),
])
def test_passwords_built_from_the_persons_details_or_the_service_name_are_refused(personal, found, source):
    """The message names the part to remove: people could not tell which part of a long password was refused."""
    problems = policy.problems(personal, email="sunita.more@example.com", mobile="+91 90000 00001", full_name="Sunita More")
    assert problems == [policy.too_personal(found, source)]
    assert problems[0].startswith(f'Password: Remove "{found}" (it comes from {source}). ')
    assert problems[0].endswith(policy.TOO_PERSONAL.removeprefix("Password: "))


@pytest.mark.parametrize("repetitive", ["aaaaaaaaaaaaaa", "abababababab", "my-12345678-key", "zz-abcdefgh-zz"])
def test_repetitive_or_sequential_passwords_are_refused(repetitive):
    assert policy.problems(repetitive) == [policy.TOO_REPETITIVE]
