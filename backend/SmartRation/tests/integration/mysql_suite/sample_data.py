"""The 100 synthetic test people, and the malicious inputs used by the security tests.

Every record is fabricated. Emails use the reserved `.test` domain; mobile numbers are
synthetic 10-digit values starting with 7. No Aadhaar numbers appear anywhere.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass

# Names chosen to stress encoding and escaping: Devanagari, accents, apostrophes, quotes,
# backslashes, 4-byte emoji, and the minimum/maximum lengths the API accepts (2 and 150).
_NAMES = [
    "Rahul Patil",
    "राहुल पाटील",                    # Marathi (Devanagari, 3-byte UTF-8)
    "Priya D'Souza",                  # apostrophe
    'Anil "Bapu" Jadhav',             # double quotes
    "Zoë Ångström-Müller",            # accented Latin
    "Sunita 🌾 Shinde",               # 4-byte emoji: needs utf8mb4, breaks utf8mb3
    "Back\\slash Kale",               # backslash
    "Semi;colon -- Wagh",             # SQL comment/terminator characters, harmless as data
    "Percent 100% _under_score",      # LIKE wildcards
    "Tab\tand\nNewline Pawar",        # control characters
    "Om",                             # 2 chars: API minimum
    "A" * 150,                        # 150 chars: API maximum
    "अ" * 150,                        # 150 multi-byte chars (450 bytes)
    "O'Brien; DROP TABLE Users; --",  # looks like injection, must be stored literally
]


@dataclass(frozen=True)
class Person:
    index: int
    full_name: str
    email: str
    mobile: str
    password: str


def people(prefix: str = "p", count: int = 100) -> list[Person]:
    """`count` deterministic, unique people. `prefix` keeps emails/mobiles unique across tests."""
    tag = zlib.crc32(prefix.encode()) % 900 + 100  # stable 3 digits, so mobiles stay 10 long
    result = []
    for i in range(count):
        name = _NAMES[i % len(_NAMES)] if i < len(_NAMES) * 2 else f"Test Person {i:03d}"
        result.append(Person(
            index=i,
            full_name=name,
            email=f"{prefix}.{i:03d}@example.test",
            mobile=f"7{tag}{i:06d}"[:10],
            password=f"Synthetic-Pass-{i:03d}!",
        ))
    return result


def long_email(length: int) -> str:
    """A syntactically valid email of exactly `length` characters."""
    domain = "@example.test"
    return "x" * (length - len(domain)) + domain


# Classic and less obvious SQL injection payloads. With bound parameters they are just text.
INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "' OR 1=1 -- ",
    "' OR 1=1 #",
    "admin@example.test'--",
    '" OR ""="',
    "'; DROP TABLE Users; --",
    "'; DELETE FROM Users WHERE '1'='1",
    "' UNION SELECT PasswordHash, Email FROM Users --",
    "1' AND SLEEP(5) AND '1'='1",
    "' OR BENCHMARK(10000000, SHA1('x')) -- ",
    "\\'; UPDATE Users SET Role=4; --",
    "%' OR Email LIKE '%",
    "x' AND (SELECT COUNT(*) FROM information_schema.tables) > 0 AND 'a'='a",
    "ʼ OR 1=1 -- ",          # modifier-letter apostrophe (charset confusion attempts)
    "' OR 'x'='x'/*",
    "0x27204f5220313d31",         # hex-encoded "' OR 1=1"
]
