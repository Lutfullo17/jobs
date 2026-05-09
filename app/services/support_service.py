"""
Biznes qoidalari: kim nima qila oladi.

- Thread yaratish: faqat HR yoki candidate.
- O'z thread'ingni ko'rish va unda javob: faqat yaratgan odam (admin boshqa yo'l bilan ko'radi).
- Admin: barcha thread'lar, javob berish, yopish.
"""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.support import SupportMessage, SupportThread, SupportThreadStatus
from app.models.user import User, UserRole


async def create_thread_with_first_message(
    db: AsyncSession,
    *,
    creator: User,
    subject: str,
    first_body: str,
) -> SupportThread:
    thread = SupportThread(created_by_id=creator.id, subject=subject.strip(), status=SupportThreadStatus.open)
    db.add(thread)
    await db.flush()
    db.add(SupportMessage(thread_id=thread.id, sender_id=creator.id, body=first_body.strip()))
    await db.commit()
    await db.refresh(thread)
    return thread


async def list_threads_for_user(db: AsyncSession, user_id: int) -> list[SupportThread]:
    result = await db.execute(
        select(SupportThread).where(SupportThread.created_by_id == user_id).order_by(SupportThread.updated_at.desc())
    )
    return list(result.scalars().all())


async def list_all_threads_admin(
    db: AsyncSession,
    *,
    status_filter: SupportThreadStatus | None = None,
) -> list[SupportThread]:
    q = select(SupportThread).order_by(SupportThread.updated_at.desc())
    if status_filter is not None:
        q = q.where(SupportThread.status == status_filter)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_thread_with_messages(
    db: AsyncSession,
    thread_id: int,
    *,
    requester: User,
) -> SupportThread:
    """
    Xavfsizlik: faqat thread egasi yoki admin ko'ra oladi.
    """
    result = await db.execute(
        select(SupportThread)
        .options(selectinload(SupportThread.messages))
        .where(SupportThread.id == thread_id)
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mavzu topilmadi.")

    if requester.role == UserRole.admin:
        return thread
    if thread.created_by_id != requester.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu murojaatni ko'rishga ruxsat yo'q.")
    return thread


async def add_user_reply(
    db: AsyncSession,
    *,
    thread_id: int,
    author: User,
    body: str,
) -> SupportMessage:
    thread = await _get_open_thread_for_owner(db, thread_id, author.id)
    msg = SupportMessage(thread_id=thread.id, sender_id=author.id, body=body.strip())
    # Ro'yxatda "oxirgi yangilanish" ko'rinishi uchun mavzuni ham yangilaymiz.
    thread.updated_at = datetime.now(UTC)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def add_admin_reply(
    db: AsyncSession,
    *,
    thread_id: int,
    admin: User,
    body: str,
) -> SupportMessage:
    if admin.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faqat admin javob berishi mumkin.")

    result = await db.execute(select(SupportThread).where(SupportThread.id == thread_id))
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mavzu topilmadi.")
    if thread.status != SupportThreadStatus.open:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Yopilgan murojaatga yozib bo'lmaydi.")

    msg = SupportMessage(thread_id=thread.id, sender_id=admin.id, body=body.strip())
    thread.updated_at = datetime.now(UTC)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def close_thread_admin(db: AsyncSession, *, thread_id: int, admin: User) -> SupportThread:
    if admin.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faqat admin yopadi.")

    result = await db.execute(select(SupportThread).where(SupportThread.id == thread_id))
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mavzu topilmadi.")

    thread.status = SupportThreadStatus.closed
    await db.commit()
    await db.refresh(thread)
    return thread


async def _get_open_thread_for_owner(db: AsyncSession, thread_id: int, owner_id: int) -> SupportThread:
    result = await db.execute(select(SupportThread).where(SupportThread.id == thread_id))
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mavzu topilmadi.")
    if thread.created_by_id != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu murojaat sizniki emas.")
    if thread.status != SupportThreadStatus.open:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Yopilgan murojaatga yozib bo'lmaydi.")
    return thread
