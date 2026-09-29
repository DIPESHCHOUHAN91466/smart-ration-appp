"""Shop stock: view, add a new item line, correct a balance, receive a delivery, write off damage.

Every balance change also writes an InventoryMovement row (see inventory_ledger) in the same commit.
Shop owners see and manage only their own shop; officials and admins any shop.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import Actor
from app.core.errors import BadRequest, Conflict, Forbidden, NotFound
from app.database.enums import InventoryMovementType, NotificationType, RationType, UserRole, parse_enum
from app.database.models import Inventory, RationShop, User
from app.services import inventory_ledger, notification_service
from app.services.mappers import inventory_dto
from app.utils.dotnet import qty_text
from app.utils.time import utc_now


def _ensure_can_manage(actor: Actor, shop_id: int) -> None:
    if actor.role == UserRole.ShopOwner:
        allowed = actor.ration_shop_id == shop_id
    else:
        allowed = actor.role in (UserRole.GovernmentOfficial, UserRole.Admin)
    if not allowed:
        raise Forbidden("You do not have permission to manage inventory for this shop.")


def _load_managed(db: Session, actor: Actor, inventory_id: int) -> Inventory:
    inventory = db.scalar(select(Inventory).where(Inventory.Id == inventory_id).with_for_update())
    if inventory is None:
        raise NotFound("Inventory record not found.")
    _ensure_can_manage(actor, inventory.RationShopId)
    return inventory


def list_for(db: Session, actor: Actor, shop_id: int | None) -> list[dict]:
    if actor.role == UserRole.ShopOwner:
        shop_id = actor.ration_shop_id
    elif actor.role not in (UserRole.GovernmentOfficial, UserRole.Admin):
        raise Forbidden("You do not have permission to view inventory.")
    q = select(Inventory)
    if shop_id is not None:
        q = q.where(Inventory.RationShopId == shop_id)
    return [inventory_dto(i) for i in db.scalars(q.order_by(Inventory.RationShopId, Inventory.RationType))]


def create(db: Session, actor: Actor, shop_id: int, ration_type: str, available: Decimal, minimum: Decimal) -> dict:
    if db.get(RationShop, shop_id) is None:
        raise NotFound("Ration shop not found.")
    _ensure_can_manage(actor, shop_id)
    rtype = parse_enum(RationType, ration_type)
    if rtype is None:
        raise BadRequest(f"Unknown ration item '{ration_type}'.")
    if db.scalar(select(Inventory.Id).where(Inventory.RationShopId == shop_id, Inventory.RationType == int(rtype))):
        raise Conflict(f"Inventory for {rtype.name} already exists at this shop. Use the update endpoint instead.")
    inventory = Inventory(RationShopId=shop_id, RationType=int(rtype), AvailableQuantity=available, AllocatedQuantity=Decimal(0),
                          MinimumStockLevel=minimum, UpdatedAt=utc_now())
    db.add(inventory)
    if available > 0:
        inventory_ledger.record(db, inventory, InventoryMovementType.Received, available, actor.user_id, note="Opening stock")
    db.commit()
    return inventory_dto(inventory)


def update(db: Session, actor: Actor, inventory_id: int, available: Decimal, minimum: Decimal) -> dict:
    inventory = _load_managed(db, actor, inventory_id)
    delta = available - inventory.AvailableQuantity
    inventory.AvailableQuantity = available
    inventory.MinimumStockLevel = minimum
    inventory.UpdatedAt = utc_now()
    if delta != 0:   # a direct balance edit is a manual correction — keep it visible in the ledger
        inventory_ledger.record(db, inventory, InventoryMovementType.Adjustment, delta, actor.user_id, note="Manual stock correction")
    if inventory.AvailableQuantity <= inventory.MinimumStockLevel:
        owners = db.scalars(select(User.Id).where(User.RationShopId == inventory.RationShopId, User.Role == int(UserRole.ShopOwner)))
        for owner_id in owners:
            notification_service.create(db, owner_id, NotificationType.LowInventory, "Low stock alert",
                                        f"{RationType(inventory.RationType).name} is running low ({qty_text(inventory.AvailableQuantity)} "
                                        f"remaining, threshold {qty_text(inventory.MinimumStockLevel)}).")
    db.commit()
    return inventory_dto(inventory)


def receive(db: Session, actor: Actor, inventory_id: int, quantity: Decimal, reference: str | None, note: str | None) -> dict:
    inventory = _load_managed(db, actor, inventory_id)
    inventory.AvailableQuantity += quantity
    inventory.UpdatedAt = utc_now()
    inventory_ledger.record(db, inventory, InventoryMovementType.Received, quantity, actor.user_id, reference, note)
    db.commit()
    return inventory_dto(inventory)


def damage(db: Session, actor: Actor, inventory_id: int, quantity: Decimal, reference: str | None, note: str | None) -> dict:
    inventory = _load_managed(db, actor, inventory_id)
    if quantity > inventory.AvailableQuantity:
        raise BadRequest(f"Cannot write off {qty_text(quantity)} — only {qty_text(inventory.AvailableQuantity)} in stock.",
                         "INSUFFICIENT_STOCK")
    inventory.AvailableQuantity -= quantity
    inventory.UpdatedAt = utc_now()
    inventory_ledger.record(db, inventory, InventoryMovementType.Damaged, quantity, actor.user_id, reference, note)
    db.commit()
    return inventory_dto(inventory)
