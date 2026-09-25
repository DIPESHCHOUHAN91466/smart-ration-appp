"""The one place synthetic (fabricated) citizen data comes from.

    from app.synthetic import generate, validate, insert
    people = generate(1000, seed=2026)    # same seed -> identical data, every time
    validate(people)                      # raises SyntheticDataError on any unsafe/invalid record
    insert(db, people, password_hash)     # bulk insert; caller commits
    book(db, people)                      # optional: one upcoming token each, capacity respected
    collect(db, people, share=0.5)        # optional: past collections + stock ledger (never below zero)

Nothing here resembles a real person's identity: mobiles are in 90xx-xxxxxx blocks the demo
accounts don't use, emails are on the reserved example.com domain (RFC 2606), Aadhaar exists only
as a masked value + an opaque reference, and every row is tagged DataSource="SYNTHETIC_DEMO".
"""

from app.synthetic.generator import (
    SOURCE,
    SyntheticDataError,
    SyntheticMember,
    SyntheticPerson,
    book,
    collect,
    generate,
    insert,
    is_synthetic_email,
    is_synthetic_mobile,
    validate,
)

__all__ = [
    "SOURCE",
    "SyntheticDataError",
    "SyntheticMember",
    "SyntheticPerson",
    "book",
    "collect",
    "generate",
    "insert",
    "is_synthetic_email",
    "is_synthetic_mobile",
    "validate",
]
