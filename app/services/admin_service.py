from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole






async def list_pending_hr_users(db: AsyncSession) -> list[User]:
    result = await db.execute(
        select(User).where(
            User.role == UserRole.hr,
            User.hr_approved.is_(False),
            User.is_active.is_(True),
        )
    )
    return list(result.scalars().all())


async def approve_hr_user(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi.")
    if user.role != UserRole.hr:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu akkaunt HR emas.")
    if user.hr_approved:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="HR allaqachon tasdiqlangan.")

    user.hr_approved = True
    await db.commit()
    await db.refresh(user)
    return user
