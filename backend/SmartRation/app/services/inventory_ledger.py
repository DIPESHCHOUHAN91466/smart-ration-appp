"""Appends an InventoryMovement row next to every stock change.

It never commits: the movement is saved in the same transaction as the Inventory balance change, so the
ledger and the balance can never disagree.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.database.enums import InventoryMovementType
from app.database.models import Inventory, InventoryMovement
from app.utils.time import utc_now


def record(db: Session, inventory: Inventory, kind: InventoryMovementType, quantity: Decimal, user_id: int | None,
           reference: str | None = None, note: str | None = None, idempotency_key: str | None = None) -> InventoryMovement:
    movement = InventoryMovement(RationShopId=inventory.RationShopId, RationType=inventory.RationType, MovementType=int(kind),
                                 Quantity=quantity, BalanceAfter=inventory.AvailableQuantity, Reference=reference,
                                 Note=note, RecordedByUserId=user_id, CreatedAt=utc_now(), IdempotencyKey=idempotency_key or None)
    db.add(movement)
    return movement
