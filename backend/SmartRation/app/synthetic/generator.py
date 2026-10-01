"""Deterministic synthetic citizens: generation, validation and bulk insertion.

Identifier formats (all clearly fabricated; `seed` and `n` shown for seed=2026, person n=1):

    mobile         90BB000001        BB = seed % 99 + 1 (01-99). Block 00 is reserved: demo accounts
                                     9000000001, -051, -052 and the C# seeder's beneficiaries 9000000002-050.
    email          user0001.s2026@example.com
    ration card    SYN-RC-2026-000001     (stored as Families.FamilyCode)
    beneficiary    SYN-BEN-2026-000001
    Aadhaar        XXXX-XXXX-1234 + reference SYN-AAD-2026-000001 (no full number exists anywhere)
    passbook       SYN-PB-2026-000001

Same (count, seed) -> byte-identical output: every random choice comes from one random.Random(seed)
and dates are relative to a fixed reference day, not "today".
"""

from __future__ import annotations

import random
import re
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import cast

from sqlalchemy import CursorResult, func, select, update
from sqlalchemy import insert as sql_insert
from sqlalchemy.orm import Session

from app.database.enums import (
    AadhaarVerificationStatus,
    EligibilityStatus,
    FamilyRelationship,
    Gender,
    MobileVerificationStatus,
    PassbookVerificationStatus,
    UserRole,
)
from app.database.models import (
    AadhaarVerification,
    Beneficiary,
    Family,
    FamilyMember,
    Inventory,
    InventoryMovement,
    MobileVerification,
    PassbookVerification,
    RationCollection,
    RationCollectionItem,
    RationItem,
    RationScheme,
    RationShop,
    SchemeEntitlementItem,
    TimeSlot,
    Token,
    TokenItem,
    User,
)
from app.utils.time import utc_now

SOURCE = "SYNTHETIC_DEMO"
TOKEN_CONFIRMED = 2              # C# TokenStatus.Confirmed (Models/Token.cs)
TOKEN_COMPLETED = 3              # C# TokenStatus.Completed
MOVEMENT_DISTRIBUTED = 2         # C# InventoryMovementType.Distributed
DEFAULT_SEED = 2026
MAX_PEOPLE = 999_999            # the mobile/code formats carry six digits of person number
MAX_FAMILY_SIZE = 6
REFERENCE_DAY = date(2026, 1, 1)
SYNTHETIC_EMAIL_DOMAINS = ("example.com", "example.org", "example.net")  # RFC 2606 reserved

_MOBILE = re.compile(r"^90\d{8}$")
_MASKED_AADHAAR = re.compile(r"^XXXX-XXXX-\d{4}$")
_CODE = re.compile(r"^SYN-(RC|BEN|AAD|PB)-\d+-\d{6}$")

# English and Devanagari (Marathi/Hindi) names, plus an apostrophe, so every generated batch also
# exercises utf8mb4 storage and quoting. Common given names/surnames, not real individuals.
_FIRST = ["Rahul", "Priya", "Amit", "Sunita", "Vijay", "Anita", "Suresh", "Kavita", "Ganesh", "Meera",
          "राहुल", "प्रिया", "सुनीता", "गणेश", "मीरा", "विजय"]
_LAST = ["Patil", "Jadhav", "Shinde", "Pawar", "Kale", "Deshmukh", "D'Souza", "More",
         "पाटील", "जाधव", "शिंदे", "पवार"]
_FAMILY_SIZES = [1, 2, 3, 4, 5, 6]
_FAMILY_SIZE_WEIGHTS = [10, 15, 25, 30, 12, 8]
_OTHER_RELATIONS = [FamilyRelationship.Spouse, FamilyRelationship.Son, FamilyRelationship.Daughter,
                    FamilyRelationship.Parent, FamilyRelationship.Other]


class SyntheticDataError(ValueError):
    """Generated or supplied synthetic data failed validation (or can't be inserted)."""

    def __init__(self, problems: Sequence[str]):
        self.problems = list(problems)
        shown = "; ".join(self.problems[:10]) + (f" (+{len(self.problems) - 10} more)" if len(self.problems) > 10 else "")
        super().__init__(f"Synthetic data rejected: {shown}")


@dataclass(frozen=True)
class SyntheticMember:
    full_name: str
    age: int
    relationship: FamilyRelationship


@dataclass(frozen=True)
class SyntheticPerson:
    number: int                      # 1-based position in the batch
    full_name: str
    email: str
    mobile: str
    gender: Gender
    date_of_birth: date
    village: str
    district: str
    state: str
    address: str
    ration_card: str                 # Families.FamilyCode
    beneficiary_code: str
    aadhaar_reference: str
    aadhaar_masked: str
    passbook_number: str
    members: tuple[SyntheticMember, ...] = field(default_factory=tuple)  # head first

    @property
    def aadhaar_last4(self) -> str:
        return self.aadhaar_masked[-4:]


def member_gender(member: SyntheticMember, person: SyntheticPerson) -> int | None:
    """Only what the data already says (no extra random draws, so a seed gives the same people as before):
    the head is the citizen, a son is male, a daughter is female; anyone else is left unrecorded (None)."""
    if member.relationship is FamilyRelationship.Head:
        return int(person.gender)
    if member.relationship is FamilyRelationship.Son:
        return int(Gender.Male)
    if member.relationship is FamilyRelationship.Daughter:
        return int(Gender.Female)
    return None


def is_synthetic_mobile(mobile: str) -> bool:
    return bool(_MOBILE.match(mobile or ""))


def is_synthetic_email(email: str) -> bool:
    local, at, domain = (email or "").rpartition("@")
    return bool(local) and at == "@" and "@" not in local and (domain in SYNTHETIC_EMAIL_DOMAINS or domain.endswith(".test"))


def _age_on_reference_day(born: date) -> int:
    return REFERENCE_DAY.year - born.year - ((REFERENCE_DAY.month, REFERENCE_DAY.day) < (born.month, born.day))


def generate(count: int, seed: int = DEFAULT_SEED) -> list[SyntheticPerson]:
    """`count` synthetic citizens, each the head of a family of 1-6. Deterministic for a given seed."""
    if not 1 <= count <= MAX_PEOPLE:
        raise SyntheticDataError([f"count must be between 1 and {MAX_PEOPLE}, got {count}"])
    if seed < 0:
        raise SyntheticDataError([f"seed must be >= 0, got {seed}"])
    rng = random.Random(seed)
    block = seed % 99 + 1
    people = []
    for n in range(1, count + 1):
        surname = rng.choice(_LAST)
        born = date(REFERENCE_DAY.year - rng.randint(18, 80), rng.randint(1, 12), rng.randint(1, 28))
        village = f"Demo Village {rng.randint(1, 50):03d}"
        size = rng.choices(_FAMILY_SIZES, _FAMILY_SIZE_WEIGHTS)[0]
        head_name = f"{rng.choice(_FIRST)} {surname}"
        members = [SyntheticMember(head_name, _age_on_reference_day(born), FamilyRelationship.Head)]
        members += [SyntheticMember(f"{rng.choice(_FIRST)} {surname}", rng.randint(0, 90), rng.choice(_OTHER_RELATIONS))
                    for _ in range(size - 1)]
        people.append(SyntheticPerson(
            number=n,
            full_name=head_name,
            email=f"user{n:04d}.s{seed}@example.com",
            mobile=f"90{block:02d}{n:06d}",
            gender=rng.choice([Gender.Male, Gender.Female, Gender.Other]),
            date_of_birth=born,
            village=village,
            district=f"Demo District {rng.randint(1, 5)}",
            state="Maharashtra",
            address=f"House {rng.randint(1, 400)}, {village}",
            ration_card=f"SYN-RC-{seed}-{n:06d}",
            beneficiary_code=f"SYN-BEN-{seed}-{n:06d}",
            aadhaar_reference=f"SYN-AAD-{seed}-{n:06d}",
            aadhaar_masked=f"XXXX-XXXX-{rng.randint(1000, 9999)}",
            passbook_number=f"SYN-PB-{seed}-{n:06d}",
            members=tuple(members),
        ))
    return people


def validate(people: Sequence[SyntheticPerson]) -> None:
    """Reject anything that is invalid, duplicated, or could be mistaken for real identity data."""
    problems: list[str] = []
    seen: dict[str, set[str]] = {"email": set(), "mobile": set(), "code": set()}

    def unique(kind: str, value: str, who: str) -> None:
        key = value.lower() if kind == "email" else value
        if key in seen[kind]:
            problems.append(f"{who}: duplicate {kind} {value}")
        seen[kind].add(key)

    for p in people:
        who = f"person {p.number}"
        if not 2 <= len(p.full_name) <= 150 or p.full_name != p.full_name.strip():
            problems.append(f"{who}: name must be 2-150 characters without surrounding spaces")
        if not is_synthetic_email(p.email) or len(p.email) > 200:
            problems.append(f"{who}: email {p.email!r} is not on a reserved test domain")
        if not is_synthetic_mobile(p.mobile) or p.mobile[2:4] == "00":
            problems.append(f"{who}: mobile {p.mobile!r} is outside the synthetic 9001-9099 blocks")
        if not _MASKED_AADHAAR.match(p.aadhaar_masked):
            problems.append(f"{who}: Aadhaar must be masked as XXXX-XXXX-1234")
        for code in (p.ration_card, p.beneficiary_code, p.aadhaar_reference, p.passbook_number):
            if not _CODE.match(code):
                problems.append(f"{who}: {code!r} is not a SYN- code")
            unique("code", code, who)
        if p.date_of_birth >= REFERENCE_DAY:
            problems.append(f"{who}: date of birth must be in the past")
        if not p.members or p.members[0].relationship is not FamilyRelationship.Head or p.members[0].full_name != p.full_name:
            problems.append(f"{who}: first family member must be the head (the person)")
        if sum(m.relationship is FamilyRelationship.Head for m in p.members) != 1 or len(p.members) > MAX_FAMILY_SIZE:
            problems.append(f"{who}: family needs exactly one head and at most {MAX_FAMILY_SIZE} members")
        if any(not 0 <= m.age <= 120 for m in p.members):
            problems.append(f"{who}: member age out of range")
        unique("email", p.email, who)
        unique("mobile", p.mobile, who)
    if problems:
        raise SyntheticDataError(problems)


def _chunks(items: Sequence, size: int) -> Iterator[Sequence]:
    for start in range(0, len(items), size):
        yield items[start:start + size]


def _ids(db: Session, column, key_column, keys: Iterable[str], size: int) -> dict[str, int]:
    found: dict[str, int] = {}
    for part in _chunks(list(keys), size):
        found.update({k: i for i, k in db.execute(select(column, key_column).where(key_column.in_(part))).all()})
    return found


def insert(db: Session, people: Sequence[SyntheticPerson], password_hash: str, batch_size: int = 500) -> dict[str, int]:
    """Validate, then bulk-insert users, families, members, beneficiaries and their mobile/Aadhaar/
    passbook verifications. Families are spread over the active shops. The caller commits (one
    transaction: all or nothing). Returns the row count per table."""
    validate(people)
    shop_ids = list(db.scalars(select(RationShop.Id).where(RationShop.IsActive.is_(True)).order_by(RationShop.Id)))
    scheme_id = db.scalar(select(RationScheme.Id).where(RationScheme.IsActive.is_(True))
                          .order_by((RationScheme.SchemeCode == "DEMO-NFSA").desc(), RationScheme.Id).limit(1))
    if not shop_ids or not scheme_id:
        raise SyntheticDataError(["no active ration shop/scheme: seed the reference data first"])

    now = utc_now()

    def bulk(model, rows: list[dict]) -> None:
        for part in _chunks(rows, batch_size):
            db.execute(sql_insert(model), list(part))

    bulk(User, [dict(FullName=p.full_name, Email=p.email, MobileNumber=p.mobile, PasswordHash=password_hash,
                     Role=int(UserRole.RuralUser), IsActive=True, CreatedAt=now) for p in people])
    user_ids = _ids(db, User.Id, User.Email, (p.email for p in people), batch_size)

    bulk(Family, [dict(FamilyCode=p.ration_card, RationShopId=shop_ids[i % len(shop_ids)], RationSchemeId=scheme_id,
                       DataSource=SOURCE, CreatedAt=now) for i, p in enumerate(people)])
    family_ids = _ids(db, Family.Id, Family.FamilyCode, (p.ration_card for p in people), batch_size)

    members = [dict(FamilyId=family_ids[p.ration_card], FullName=m.full_name, Age=m.age, Relationship=int(m.relationship),
                    Eligibility=int(EligibilityStatus.Eligible), DataSource=SOURCE, Gender=member_gender(m, p))
               for p in people for m in p.members]
    bulk(FamilyMember, members)

    bulk(Beneficiary, [dict(BeneficiaryCode=p.beneficiary_code, Address=p.address, Gender=int(p.gender),
                            DateOfBirth=datetime.combine(p.date_of_birth, datetime.min.time()), Village=p.village,
                            District=p.district, State=p.state, Pincode="", ProfilePhotoUrl=None,
                            UserId=user_ids[p.email], FamilyId=family_ids[p.ration_card], IsActive=True, IsBlocked=False,
                            DataSource=SOURCE, CreatedAt=now) for p in people])
    beneficiary_ids = _ids(db, Beneficiary.Id, Beneficiary.BeneficiaryCode, (p.beneficiary_code for p in people), batch_size)

    bulk(MobileVerification, [dict(BeneficiaryId=beneficiary_ids[p.beneficiary_code], MobileMasked="******" + p.mobile[-4:],
                                   Status=int(MobileVerificationStatus.Verified), VerifiedAt=now, VerificationSource=SOURCE)
                              for p in people])
    bulk(AadhaarVerification, [dict(BeneficiaryId=beneficiary_ids[p.beneficiary_code], AadhaarReferenceId=p.aadhaar_reference,
                                    AadhaarMasked=p.aadhaar_masked, Status=int(AadhaarVerificationStatus.Verified),
                                    VerificationDate=now, VerificationSource=SOURCE, VerificationMode="PRE_VERIFIED")
                               for p in people])
    bulk(PassbookVerification, [dict(BeneficiaryId=beneficiary_ids[p.beneficiary_code], PassbookNumber=p.passbook_number,
                                     Status="ACTIVE", VerificationStatus=int(PassbookVerificationStatus.Verified),
                                     LastUpdated=now, VerificationSource=SOURCE) for p in people])
    db.flush()
    n = len(people)
    return {"Users": n, "Families": n, "FamilyMembers": len(members), "Beneficiaries": n,
            "MobileVerifications": n, "AadhaarVerifications": n, "PassbookVerifications": n}


@dataclass(frozen=True)
class _Citizen:
    user_id: int
    beneficiary_id: int
    shop_id: int
    scheme_id: int


def _citizens(db: Session, people: Sequence[SyntheticPerson], batch_size: int = 1000) -> list[_Citizen]:
    """The inserted rows behind `people`, in the same order (batched: large IN lists are slow)."""
    found: dict[str, _Citizen] = {}
    for part in _chunks([p.email for p in people], batch_size):
        for email, user_id, beneficiary_id, shop_id, scheme_id in db.execute(
                select(User.Email, User.Id, Beneficiary.Id, Family.RationShopId, Family.RationSchemeId)
                .join(Beneficiary, Beneficiary.UserId == User.Id).join(Family, Family.Id == Beneficiary.FamilyId)
                .where(User.Email.in_(list(part)))):
            found[email] = _Citizen(user_id, beneficiary_id, shop_id, scheme_id)
    if len(found) != len(people):
        raise SyntheticDataError(["insert the citizens before booking or collecting for them"])
    return [found[p.email] for p in people]


def _entitlements(db: Session) -> tuple[dict[int, Decimal], dict[int, list[int]]]:
    """(standard quota per active ration type, entitled ration types per scheme) - what a token carries."""
    quotas = {t: q for t, q in db.execute(select(RationItem.RationType, RationItem.StandardQuotaPerBooking)
                                          .where(RationItem.IsActive.is_(True)))}
    entitled: dict[int, list[int]] = {}
    for scheme_id, ration_type in db.execute(select(SchemeEntitlementItem.RationSchemeId, SchemeEntitlementItem.RationType)
                                             .order_by(SchemeEntitlementItem.RationSchemeId, SchemeEntitlementItem.RationType)):
        if ration_type in quotas:
            entitled.setdefault(scheme_id, []).append(ration_type)
    return quotas, entitled


def book(db: Session, people: Sequence[SyntheticPerson]) -> dict[str, int]:
    """Give each (already inserted) citizen one Confirmed token in the earliest free upcoming slot at
    their family's shop, like the C# BookingService: capacity respected, BookedCount raised, token
    number SR-<year>-<id>, items = the scheme's entitled ration types at their standard quota. The QR
    value is left empty; the C# API signs it on first request. Caller commits. Citizens whose shop
    has no free upcoming slot are counted as "Unbooked"."""
    today = datetime.combine(utc_now().date(), datetime.min.time())
    rows = [(c.user_id, c.shop_id, c.scheme_id) for c in _citizens(db, people)]
    quotas, entitled = _entitlements(db)

    free: dict[int, list[list[int]]] = {}   # shop -> [[slot id, places left], ...] earliest first
    for slot_id, shop_id, capacity, booked in db.execute(
            select(TimeSlot.Id, TimeSlot.RationShopId, TimeSlot.Capacity, TimeSlot.BookedCount)
            .where(TimeSlot.SlotDate >= today, TimeSlot.BookedCount < TimeSlot.Capacity)
            .order_by(TimeSlot.SlotDate, TimeSlot.StartTime, TimeSlot.Id)):
        free.setdefault(shop_id, []).append([slot_id, capacity - booked])

    now = utc_now()
    taken: dict[int, int] = {}
    tokens: list[tuple[Token, int]] = []
    for user_id, shop_id, scheme_id in rows:
        slots = free.get(shop_id, [])
        while slots and slots[0][1] == 0:
            slots.pop(0)
        if not slots:
            continue
        slots[0][1] -= 1
        taken[slots[0][0]] = taken.get(slots[0][0], 0) + 1
        token = Token(TokenNumber=f"PENDING-{user_id}-{now:%H%M%S%f}", UserId=user_id, RationShopId=shop_id,
                      TimeSlotId=slots[0][0], Status=TOKEN_CONFIRMED, QRCodeValue=None, CreatedAt=now)
        db.add(token)
        tokens.append((token, scheme_id))
    db.flush()
    items = 0
    for token, scheme_id in tokens:
        token.TokenNumber = f"SR-{token.CreatedAt:%Y}-{token.Id:06d}"
        for ration_type in entitled.get(scheme_id, []):
            db.add(TokenItem(TokenId=token.Id, RationType=ration_type, Quantity=quotas[ration_type]))
            items += 1
    for slot_id, count in taken.items():
        result = db.execute(update(TimeSlot).where(TimeSlot.Id == slot_id, TimeSlot.BookedCount + count <= TimeSlot.Capacity)
                            .values(BookedCount=TimeSlot.BookedCount + count))
        moved = cast(CursorResult, result).rowcount
        if moved != 1:
            raise SyntheticDataError([f"slot {slot_id} changed while booking; nothing was booked"])
    db.flush()
    return {"Tokens": len(tokens), "TokenItems": items, "Unbooked": len(people) - len(tokens)}


def collect(db: Session, people: Sequence[SyntheticPerson], share: float = 0.5) -> dict[str, int]:
    """Past collections (the "transaction" history) for the first `share` of the (already inserted)
    citizens, following the C# RationCollectionService rules: a Completed token in a past slot at the
    family's shop (capacity respected), a RationCollection with its items, stock moved from available
    to allocated with a Distributed ledger entry per item, and never below zero - a citizen whose shop
    lacks the stock is skipped ("NotCollected"). Operator = the shop's owner account if one exists,
    else 0 (the generator). Caller commits."""
    if not 0 <= share <= 1:
        raise SyntheticDataError([f"share must be between 0 and 1, got {share}"])
    chosen = _citizens(db, people)[:round(len(people) * share)]
    today = datetime.combine(utc_now().date(), datetime.min.time())
    quotas, entitled = _entitlements(db)
    operators: dict[int, int] = {shop: user for shop, user in db.execute(
        select(User.RationShopId, func.min(User.Id))
        .where(User.Role == int(UserRole.ShopOwner), User.RationShopId.is_not(None))
        .group_by(User.RationShopId)) if shop is not None}
    stock = {(i.RationShopId, i.RationType): i for i in db.scalars(select(Inventory))}
    slots: dict[int, list[TimeSlot]] = {}
    for slot in db.scalars(select(TimeSlot).where(TimeSlot.SlotDate < today, TimeSlot.BookedCount < TimeSlot.Capacity)
                           .order_by(TimeSlot.SlotDate, TimeSlot.StartTime, TimeSlot.Id)):
        slots.setdefault(slot.RationShopId, []).append(slot)

    done: list[tuple[Token, RationCollection]] = []
    skipped = 0
    for citizen in chosen:
        free = slots.get(citizen.shop_id, [])
        while free and free[0].BookedCount >= free[0].Capacity:
            free.pop(0)
        items = [(t, quotas[t]) for t in entitled.get(citizen.scheme_id, []) if (citizen.shop_id, t) in stock]
        if not free or not items or any(stock[(citizen.shop_id, t)].AvailableQuantity < q for t, q in items):
            skipped += 1
            continue
        slot = free[0]
        slot.BookedCount += 1
        at = datetime.combine(slot.SlotDate.date(), slot.StartTime)
        operator = operators.get(citizen.shop_id, 0)
        token = Token(TokenNumber=f"PENDING-{citizen.user_id}-C", UserId=citizen.user_id, RationShopId=citizen.shop_id,
                      TimeSlotId=slot.Id, Status=TOKEN_COMPLETED, QRCodeValue=None, CreatedAt=at, CollectedAt=at)
        collection = RationCollection(CollectionCode=f"PENDING-{citizen.user_id}-C", BeneficiaryId=citizen.beneficiary_id,
                                      RationShopId=citizen.shop_id, OperatorUserId=operator, VerificationMethod="QR",
                                      CollectedAt=at, IdempotencyKey=None)
        db.add(token)
        db.flush()
        collection.TokenId = token.Id
        token.TokenNumber = f"SR-{at:%Y}-{token.Id:06d}"
        db.add(collection)
        db.flush()
        collection.CollectionCode = f"COL-SYN-{collection.Id:06d}"
        for ration_type, quantity in items:
            db.add(TokenItem(TokenId=token.Id, RationType=ration_type, Quantity=quantity))
            db.add(RationCollectionItem(RationCollectionId=collection.Id, RationType=ration_type, Quantity=quantity))
            inventory = stock[(citizen.shop_id, ration_type)]
            inventory.AvailableQuantity -= quantity
            inventory.AllocatedQuantity += quantity
            inventory.UpdatedAt = at
            db.add(InventoryMovement(RationShopId=citizen.shop_id, RationType=ration_type, MovementType=MOVEMENT_DISTRIBUTED,
                                     Quantity=quantity, BalanceAfter=inventory.AvailableQuantity, Reference=token.TokenNumber,
                                     Note="synthetic collection", RecordedByUserId=operator or None, CreatedAt=at))
        done.append((token, collection))
    db.flush()
    return {"Collections": len(done), "NotCollected": skipped, "NotSelected": len(people) - len(chosen)}
