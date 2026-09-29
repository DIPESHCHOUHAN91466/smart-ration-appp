"""In-app notifications (booking confirmations, cancellations, collections, low stock, AI alerts).

`create` only adds the row to the caller's session, so a notification is saved in the same
transaction as the change it announces. Delivery by SMS is not part of this (see otp_service).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import Actor
from app.database.enums import NotificationType
from app.database.models import Notification
from app.utils.dotnet import dt
from app.utils.time import utc_now


def create(db: Session, user_id: int, kind: NotificationType, title: str, message: str) -> None:
    db.add(Notification(UserId=user_id, Type=int(kind), Title=title, Message=message, IsRead=False, CreatedAt=utc_now()))


def list_for(db: Session, actor: Actor) -> list[dict]:
    rows = db.scalars(select(Notification).where(Notification.UserId == actor.user_id)
                      .order_by(Notification.CreatedAt.desc(), Notification.Id.desc())).all()
    return [{"id": n.Id, "type": NotificationType(n.Type).name, "title": n.Title, "message": n.Message,
             "isRead": bool(n.IsRead), "createdAt": dt(n.CreatedAt)} for n in rows]


def mark_read(db: Session, actor: Actor, ids: list[int]) -> None:
    """Only the caller's own notifications can be marked; other ids are ignored."""
    for n in db.scalars(select(Notification).where(Notification.UserId == actor.user_id, Notification.Id.in_(ids))):
        n.IsRead = True
    db.commit()
