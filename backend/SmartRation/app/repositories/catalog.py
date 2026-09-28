"""Public reference data: active ration shops, ration items and schemes with their entitlements.
Nothing here is personal data, which is why the Public Help chatbot may read it."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RationItem, RationScheme, RationShop, SchemeEntitlementItem


def active_shops(db: Session) -> Sequence[RationShop]:
    return db.scalars(select(RationShop).where(RationShop.IsActive.is_(True)).order_by(RationShop.ShopName)).all()


def first_active_shop_id(db: Session) -> int | None:
    return db.scalar(select(RationShop.Id).where(RationShop.IsActive.is_(True)).order_by(RationShop.Id).limit(1))


def active_items(db: Session) -> Sequence[RationItem]:
    return db.scalars(select(RationItem).where(RationItem.IsActive.is_(True))).all()


def active_schemes(db: Session) -> Sequence[RationScheme]:
    return db.scalars(select(RationScheme).where(RationScheme.IsActive.is_(True)).order_by(RationScheme.SchemeCode)).all()


def active_scheme_id(db: Session, scheme_code: str) -> int | None:
    return db.scalar(select(RationScheme.Id).where(RationScheme.SchemeCode == scheme_code, RationScheme.IsActive.is_(True)).limit(1))


def scheme_entitlements(db: Session, scheme_id: int) -> Sequence[SchemeEntitlementItem]:
    return db.scalars(select(SchemeEntitlementItem).where(SchemeEntitlementItem.RationSchemeId == scheme_id)
                      .order_by(SchemeEntitlementItem.RationType)).all()
