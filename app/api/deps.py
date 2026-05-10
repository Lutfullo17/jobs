from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kirish tokeni noto'g'ri.") from exc

    if payload.get("token_type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token turi noto'g'ri.")

    raw_user_id = payload.get("user_id")
    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kirish tokenining yuklamasi noto'g'ri. Sizning ID-siz yo'q.") from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faol bo'lmagan foydalanuvchi.")
    return user


def require_role(*roles: UserRole):
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruxsat berilmagan.")
        return current_user

    return checker


async def require_hr_user(current_user: User = Depends(get_current_user)) -> User:
    """Faqat HR (tasdiqlangan yoki yo'q — masalan `/api/hr/status`)."""
    if current_user.role != UserRole.hr:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faqat HR uchun.")
    return current_user


async def require_candidate(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.candidate:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faqat nomzod uchun.")
    return current_user


async def require_hr_or_candidate(current_user: User = Depends(get_current_user)) -> User:
    """Admin bilan yozishmalar: faqat HR yoki nomzod (admin alohida endpoint orqali javob beradi)."""
    if current_user.role not in (UserRole.hr, UserRole.candidate):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu bo'limga faqat HR yoki nomzod kira oladi.",
        )
    return current_user


async def require_approved_hr(current_user: User = Depends(get_current_user)) -> User:
    """Vakansiya kabi HR-only amallar: rol HR va admin tasdiqlashi bo‘lishi kerak."""
    if current_user.role != UserRole.hr:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faqat HR uchun.")
    if not current_user.hr_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HR akkauntingiz admin tomonidan tasdiqlanmagan. Vakansiya joylash mumkin emas.",
        )
    return current_user
