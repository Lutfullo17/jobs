from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.models.user import User, UserRole
from app.schemas.admin import PendingHrOut
from app.schemas.auth import UserOut
from app.services.admin_service import approve_hr_user, list_pending_hr_users

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
