"""
HR va nomzodlar admin bilan yozishadi.

URL prefiks: /api/support
Authorization: Bearer (login qilgan foydalanuvchi), rol HR yoki candidate bo'lishi kerak.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_hr_or_candidate
from app.models.user import User
from app.schemas.support import (
    SupportMessageOut,
    SupportReplyBody,
    SupportReplyResponse,
    SupportThreadCreate,
    SupportThreadDetail,
    SupportThreadListItem,
)
from app.services.support_service import (
    add_user_reply,
    create_thread_with_first_message,
    get_thread_with_messages,
    list_threads_for_user,
)

router = APIRouter(prefix="/api/support", tags=["Support (HR / Candidate)"])


@router.post("/threads/", response_model=SupportThreadListItem, status_code=201)
async def open_thread(
    payload: SupportThreadCreate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_hr_or_candidate),
) -> SupportThreadListItem:
    """Yangi murojaat: mavzu + birinchi xabar admin kotibiyatiga tushadi."""
    thread = await create_thread_with_first_message(
        db,
        creator=current,
        subject=payload.subject,
        first_body=payload.message,
    )
    return SupportThreadListItem.model_validate(thread)


@router.get("/threads/", response_model=list[SupportThreadListItem])
async def my_threads(
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_hr_or_candidate),
) -> list[SupportThreadListItem]:
    """Faqat o'zing ochgan murojaatlar ro'yxati."""
    threads = await list_threads_for_user(db, current.id)
    return [SupportThreadListItem.model_validate(t) for t in threads]


@router.get("/threads/{thread_id}/", response_model=SupportThreadDetail)
async def thread_detail(
    thread_id: int,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_hr_or_candidate),
) -> SupportThreadDetail:
    """Bitta murojaat + barcha xabarlar (faqat o'zingiki)."""
    t = await get_thread_with_messages(db, thread_id, requester=current)
    msgs = sorted(t.messages, key=lambda m: m.created_at)
    return SupportThreadDetail(
        id=t.id,
        subject=t.subject,
        status=t.status,
        created_by_id=t.created_by_id,
        created_at=t.created_at,
        updated_at=t.updated_at,
        messages=[SupportMessageOut.model_validate(m) for m in msgs],
    )


@router.post("/threads/{thread_id}/messages/", response_model=SupportReplyResponse)
async def reply_to_thread(
    thread_id: int,
    payload: SupportReplyBody,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_hr_or_candidate),
) -> SupportReplyResponse:
    """Murojaat ochiq bo'lsa, yana xabar yozish (masalan qo'shimcha savol)."""
    await add_user_reply(db, thread_id=thread_id, author=current, body=payload.message)
    return SupportReplyResponse(message="Xabar yuborildi.")
