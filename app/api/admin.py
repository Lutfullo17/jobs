from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.models.support import SupportThread, SupportThreadStatus
from app.models.user import User, UserRole
from app.schemas.admin import PendingHrOut
from app.schemas.auth import UserOut
from app.schemas.support import (
    SupportMessageOut,
    SupportReplyBody,
    SupportReplyResponse,
    SupportThreadAdminListItem,
    SupportThreadDetail,
)
from app.services.admin_service import approve_hr_user, list_pending_hr_users
from app.services.support_service import (
    add_admin_reply,
    close_thread_admin,
    get_thread_with_messages,
    list_all_threads_admin,
    reload_support_thread_with_creator,
)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/pending-hr/", response_model=list[PendingHrOut])
async def pending_hr_list(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
) -> list[PendingHrOut]:
    users = await list_pending_hr_users(db)
    return [PendingHrOut.model_validate(u) for u in users]


@router.post("/hr/{user_id}/approve/", response_model=UserOut)
async def approve_hr(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
) -> UserOut:
    user = await approve_hr_user(db, user_id)
    return UserOut.model_validate(user)


# ---- Admin: HR va nomzodlardan kelgan murojaatlar (support) ----


def _support_thread_admin_list_item(t: SupportThread) -> SupportThreadAdminListItem:
    c = t.creator
    return SupportThreadAdminListItem(
        id=t.id,
        subject=t.subject,
        status=t.status,
        created_by_id=t.created_by_id,
        creator_role=c.role,
        creator_email=c.email,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.get("/support/threads/", response_model=list[SupportThreadAdminListItem])
async def admin_list_support_threads(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
    status_filter: SupportThreadStatus | None = Query(None, alias="status"),
) -> list[SupportThreadAdminListItem]:
    """
    Barcha yozishmalar.
    Ixtiyoriy filter: ?status=open yoki ?status=closed
    """
    threads = await list_all_threads_admin(db, status_filter=status_filter)
    return [_support_thread_admin_list_item(t) for t in threads]


@router.get("/support/threads/{thread_id}/", response_model=SupportThreadDetail)
async def admin_thread_detail(
    thread_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.admin)),
) -> SupportThreadDetail:
    t = await get_thread_with_messages(db, thread_id, requester=admin_user)
    msgs = sorted(t.messages, key=lambda m: m.created_at)
    creator = t.creator
    return SupportThreadDetail(
        id=t.id,
        subject=t.subject,
        status=t.status,
        created_by_id=t.created_by_id,
        creator_role=creator.role,
        creator_email=creator.email,
        created_at=t.created_at,
        updated_at=t.updated_at,
        messages=[SupportMessageOut.model_validate(m) for m in msgs],
    )


@router.post("/support/threads/{thread_id}/messages/", response_model=SupportReplyResponse)
async def admin_reply(
    thread_id: int,
    payload: SupportReplyBody,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.admin)),
) -> SupportReplyResponse:
    await add_admin_reply(db, thread_id=thread_id, admin=admin_user, body=payload.message)
    return SupportReplyResponse(message="Javob yuborildi.")


@router.post("/support/threads/{thread_id}/close/", response_model=SupportThreadAdminListItem)
async def admin_close_thread(
    thread_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.admin)),
) -> SupportThreadAdminListItem:
    """Tugagan murojaatni yopish (yangi xabar yozish mumkin bo'lmasligi uchun)."""
    await close_thread_admin(db, thread_id=thread_id, admin=admin_user)
    t = await reload_support_thread_with_creator(db, thread_id)
    return _support_thread_admin_list_item(t)


# Asosiy vazifalari:

# HR userlarni tasdiqlash
# Support murojaatlarni ko‘rish
# Chatdagi xabarlarni olish
# Javob yozish
# Murojaatni yopish