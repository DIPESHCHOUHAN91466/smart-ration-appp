"""What a family may collect this month, and today.

Monthly entitlement per item = the scheme's quota per eligible member x the number of eligible members.
Remaining = entitlement - what the family's beneficiaries already collected this calendar month (UTC).
Today's allocation = remaining, capped at the item's standard quota per visit.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import BadRequest, NotFound
from app.database.enums import EligibilityStatus, RationType
from app.database.models import (
    Beneficiary,
    Family,
    FamilyMember,
    RationCollection,
    RationCollectionItem,
    RationItem,
    RationScheme,
    SchemeEntitlementItem,
)
from app.utils.dotnet import num
from app.utils.time import utc_now


def get_entitlement(db: Session, family_id: int) -> dict:
    family = db.get(Family, family_id)
    if family is None:
        raise NotFound("Family not found.")
    scheme = db.get(RationScheme, family.RationSchemeId)
    members = db.scalars(select(FamilyMember).where(FamilyMember.FamilyId == family_id)).all()
    eligible = sum(1 for m in members if m.Eligibility == EligibilityStatus.Eligible)
    beneficiary_ids = db.scalars(select(Beneficiary.Id).where(Beneficiary.FamilyId == family_id)).all()

    now = utc_now()
    month_start = datetime(now.year, now.month, 1)
    month_end = datetime(now.year + (now.month == 12), now.month % 12 + 1, 1)
    collected: dict[int, Decimal] = {}
    if beneficiary_ids:
        rows = db.execute(
            select(RationCollectionItem.RationType, RationCollectionItem.Quantity)
            .join(RationCollection, RationCollection.Id == RationCollectionItem.RationCollectionId)
            .where(RationCollection.BeneficiaryId.in_(beneficiary_ids),
                   RationCollection.CollectedAt >= month_start, RationCollection.CollectedAt < month_end)
        ).all()
        for rtype, qty in rows:
            collected[rtype] = collected.get(rtype, Decimal(0)) + Decimal(qty)

    visit_caps = {r.RationType: Decimal(r.StandardQuotaPerBooking) for r in db.scalars(select(RationItem).where(RationItem.IsActive.is_(True)))}
    rules = db.scalars(select(SchemeEntitlementItem).where(SchemeEntitlementItem.RationSchemeId == family.RationSchemeId)
                       .order_by(SchemeEntitlementItem.Id)).all() if scheme else []
    items = []
    for rule in rules:
        monthly = Decimal(rule.QuotaPerEligibleMemberPerMonth) * eligible
        already = collected.get(rule.RationType, Decimal(0))
        remaining = max(Decimal(0), monthly - already)
        today = min(remaining, visit_caps.get(rule.RationType, remaining))
        items.append({"rationType": RationType(rule.RationType).name, "monthlyEntitlement": num(monthly),
                      "alreadyCollected": num(already), "remaining": num(remaining), "todayAllocation": num(today)})
    return {"schemeCode": scheme.SchemeCode if scheme else "", "schemeName": scheme.Name if scheme else "",
            "familySize": len(members), "eligibleMemberCount": eligible, "items": items}


def ensure_request_within_entitlement(entitlement: dict, requested: Iterable[tuple[RationType, Decimal]]) -> None:
    allowed = {i["rationType"]: Decimal(str(i["todayAllocation"])) for i in entitlement["items"]}
    for rtype, qty in requested:
        if qty < 0:
            raise BadRequest("Requested quantity cannot be negative.", "INVALID_QUANTITY")
        # An item outside the scheme has an allowance of zero.
        if qty > allowed.get(RationType(rtype).name, Decimal(0)):
            raise BadRequest("Requested quantity exceeds the beneficiary entitlement.", "ENTITLEMENT_EXCEEDED")
