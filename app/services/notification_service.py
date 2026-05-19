from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import Notification, NotificationType


async def create_notification(
    db: AsyncSession,
    *,
    user_id: int,
    ntype: NotificationType,
    title: str,
    body: str = "",
    related_entity_type: str | None = None,
    related_entity_id: int | None = None,
) -> Notification:
    row = Notification(
        user_id=user_id,
        type=ntype,
        title=title,
        body=body,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
    )
    db.add(row)
    await db.flush()
    return row


async def list_notifications(db: AsyncSession, user_id: int, *, unread_only: bool = False) -> list[Notification]:
    stmt = select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc())
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def mark_notification_read(db: AsyncSession, notification_id: int, user_id: int) -> None:
    await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
        .values(is_read=True)
    )
    await db.commit()


async def count_unread(db: AsyncSession, user_id: int) -> int:
    res = await db.execute(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id, Notification.is_read.is_(False)
        )
    )
    return int(res.scalar_one())
