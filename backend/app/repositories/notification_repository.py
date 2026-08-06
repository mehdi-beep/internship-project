from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.notification import Notification


def list_query(user_id: int) -> Select:
    # Ch.70 — unread-first, most recent first within each group.
    return (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.read.asc(), Notification.created_at.desc())
    )


def get(db: Session, notification_id: int) -> Notification | None:
    return db.get(Notification, notification_id)


def create(
    db: Session,
    *,
    user_id: int,
    title: str,
    message: str,
    related_intervention_id: int | None = None,
    related_planning_id: int | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        related_intervention_id=related_intervention_id,
        related_planning_id=related_planning_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def mark_read(db: Session, notification: Notification) -> Notification:
    notification.read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(db: Session, user_id: int) -> int:
    stmt = select(Notification).where(Notification.user_id == user_id, Notification.read.is_(False))
    unread = db.scalars(stmt).all()
    for notification in unread:
        notification.read = True
    db.commit()
    return len(unread)
