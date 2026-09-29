"""The ration item list shown when booking.

With a shopId it adds each item's available stock at that shop (read-only; never the shop's minimum
stock level). For a citizen it adds how much their family can still collect this month under their
scheme (entitlement-driven, never a hard-coded quota).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import Actor
from app.database.enums import RationType, UserRole
from app.database.models import Beneficiary, Inventory, RationItem, RationShop
from app.services import entitlement_service
from app.utils.dotnet import num


def items(db: Session, actor: Actor, shop_id: int | None) -> list[dict]:
    rows = db.scalars(select(RationItem).where(RationItem.IsActive.is_(True)).order_by(RationItem.Id)).all()
    out = [{"id": r.Id, "rationType": RationType(r.RationType).name, "name": r.Name, "vernacularName": r.VernacularName,
            "unit": r.Unit, "standardQuotaPerBooking": num(r.StandardQuotaPerBooking),
            "availableQuantity": None, "eligibleQuantity": None} for r in rows]
    if shop_id is not None:
        stock = {RationType(i.RationType).name: i.AvailableQuantity
                 for i in db.scalars(select(Inventory).where(Inventory.RationShopId == shop_id))}
        for item in out:
            if item["rationType"] in stock:
                item["availableQuantity"] = num(stock[item["rationType"]])
    if actor.role == UserRole.RuralUser:
        family_id = db.scalar(select(Beneficiary.FamilyId).where(Beneficiary.UserId == actor.user_id).limit(1))
        if family_id is not None:
            remaining = {i["rationType"]: i["remaining"] for i in entitlement_service.get_entitlement(db, family_id)["items"]}
            for item in out:
                if item["rationType"] in remaining:
                    item["eligibleQuantity"] = remaining[item["rationType"]]
    return out


def active_shops(db: Session) -> list[dict]:
    shops = db.scalars(select(RationShop).where(RationShop.IsActive.is_(True)).order_by(RationShop.ShopName)).all()
    return [{"id": s.Id, "shopName": s.ShopName, "shopCode": s.ShopCode, "address": s.Address,
             "district": s.District, "state": s.State, "isActive": bool(s.IsActive)} for s in shops]
