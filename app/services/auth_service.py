from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_code,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.email_verification_code import EmailVerificationCode
from app.models.password_reset_code import PasswordResetCode
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from app.services.email_service import send_password_reset_code, send_verification_code


async def register_user(db: AsyncSession, payload: RegisterRequest) -> User:
    if payload.role == UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator roli bu yerda ro'yxatdan o'tolmaydi.")
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Parol bir-biriga mos kelmayapti.")

    user_result = await db.execute(select(User).where(User.email == payload.email))
    if user_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Elektron pochta allaqachon mavjud.")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()

    await _create_and_send_verification_code(db, user)
    await db.commit()
    await db.refresh(user)
    return user


async def verify_email(db: AsyncSession, payload: VerifyEmailRequest) -> None:
    user_result = await db.execute(select(User).where(User.email == payload.email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi.")

    code_result = await db.execute(
        select(EmailVerificationCode)
        .where(
            and_(
                EmailVerificationCode.user_id == user.id,
                EmailVerificationCode.code == payload.code,
                EmailVerificationCode.is_used.is_(False),
            )
        )
        .order_by(EmailVerificationCode.created_at.desc())
    )
    code_obj = code_result.scalars().first()
    if not code_obj:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "Tasdiqlash kodi noto'g'ri.")
    if code_obj.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tasdiqlash kodi muddati tugagan.")

    code_obj.is_used = True
    user.is_verified = True
    await db.commit()


async def resend_verification_code(db: AsyncSession, email: str) -> None:
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi.")
    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Foydalanuvchi allaqachon tekshirilgan.")

    one_minute_ago = datetime.now(UTC) - timedelta(minutes=1)
    rate_result = await db.execute(
        select(EmailVerificationCode)
        .where(and_(EmailVerificationCode.user_id == user.id, EmailVerificationCode.created_at >= one_minute_ago))
        .order_by(EmailVerificationCode.created_at.desc())
    )
    if rate_result.scalars().first():
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="1 daqiqadan keyin yana urinib ko'ring.")

    await _create_and_send_verification_code(db, user)
    await db.commit()


async def login_user(
    db: AsyncSession,
    payload: LoginRequest,
    user_agent: str | None,
    ip_address: str | None,
) -> tuple[str, str, User]:
    user_result = await db.execute(select(User).where(User.email == payload.email))
    user = user_result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Noto'g'ri ma'lumotlar.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faol bo'lmagan foydalanuvchi.")
    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Elektron pochta tasdiqlanmagan.")

    access_token = create_access_token(str(user.id), user.email, user.role.value)
    jti = str(uuid4())
    refresh_token = create_refresh_token(str(user.id), jti)

    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at,
            revoked_at=None,
            user_agent=user_agent,
            ip_address=ip_address,
        )
    )
    await db.commit()
    return access_token, refresh_token, user


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> tuple[str, str]:
    payload = _decode_refresh_token(refresh_token)
    user_id = payload["user_id"]

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Yangilash token foydalanuvchisi noto'g'ri.")

    token_result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token)))
    token_obj = token_result.scalar_one_or_none()
    if not token_obj or token_obj.revoked_at is not None or token_obj.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Yangilash tokenining muddati tugagan yoki bekor qilingan.")

    token_obj.revoked_at = datetime.now(UTC)

    new_access_token = create_access_token(str(user.id), user.email, user.role.value)
    new_jti = str(uuid4())
    new_refresh_token = create_refresh_token(str(user.id), new_jti)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(new_refresh_token),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
            revoked_at=None,
            user_agent=token_obj.user_agent,
            ip_address=token_obj.ip_address,
        )
    )
    await db.commit()
    return new_access_token, new_refresh_token


async def logout(db: AsyncSession, refresh_token: str) -> None:
    token_hash_value = hash_token(refresh_token)
    token_result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash_value))
    token_obj = token_result.scalar_one_or_none()
    if token_obj and token_obj.revoked_at is None:
        token_obj.revoked_at = datetime.now(UTC)
        await db.commit()


async def logout_all_devices(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        update(RefreshToken)
        .where(and_(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)))
        .values(revoked_at=datetime.now(UTC))
    )
    await db.commit()
    return result.rowcount or 0


async def change_password(db: AsyncSession, current_user: User, payload: ChangePasswordRequest) -> None:
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Eski parol noto'g'ri.")
    if payload.new_password != payload.confirm_new_password:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Parol bir-biriga mos kelmayapti.")
    if verify_password(payload.new_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Yangi parol eski paroldan foydalanilishi mumkin emas.")

    current_user.password_hash = hash_password(payload.new_password)
    await db.execute(
        update(RefreshToken)
        .where(and_(RefreshToken.user_id == current_user.id, RefreshToken.revoked_at.is_(None)))
        .values(revoked_at=datetime.now(UTC))
    )
    await db.commit()


async def forgot_password(db: AsyncSession, payload: ForgotPasswordRequest) -> None:
    user_result = await db.execute(select(User).where(User.email == payload.email))
    user = user_result.scalar_one_or_none()
    if not user:
        return

    await db.execute(
        update(PasswordResetCode).where(
            and_(PasswordResetCode.user_id == user.id, PasswordResetCode.is_used.is_(False))
        ).values(is_used=True)
    )
    code = generate_code()
    db.add(
        PasswordResetCode(
            user_id=user.id,
            code=code,
            expires_at=datetime.now(UTC) + timedelta(minutes=settings.reset_code_expire_minutes),
            is_used=False,
        )
    )
    await db.commit()
    await send_password_reset_code(user.email, code)


async def reset_password(db: AsyncSession, payload: ResetPasswordRequest) -> None:
    if payload.new_password != payload.confirm_new_password:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Parol bir-biriga mos kelmayapti.")

    user_result = await db.execute(select(User).where(User.email == payload.email))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foydalanuvchi topilmadi.")

    code_result = await db.execute(
        select(PasswordResetCode)
        .where(
            and_(
                PasswordResetCode.user_id == user.id,
                PasswordResetCode.code == payload.code,
                PasswordResetCode.is_used.is_(False),
            )
        )
        .order_by(PasswordResetCode.created_at.desc())
    )
    code_obj = code_result.scalars().first()
    if not code_obj:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parol tiklash kodi noto'g'ri.")
    if code_obj.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parol tiklash kodi muddati tugagan.")

    user.password_hash = hash_password(payload.new_password)
    code_obj.is_used = True
    await db.execute(
        update(RefreshToken)
        .where(and_(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)))
        .values(revoked_at=datetime.now(UTC))
    )
    await db.commit()


async def _create_and_send_verification_code(db: AsyncSession, user: User) -> None:
    await db.execute(
        update(EmailVerificationCode)
        .where(and_(EmailVerificationCode.user_id == user.id, EmailVerificationCode.is_used.is_(False)))
        .values(is_used=True)
    )
    code = generate_code()
    db.add(
        EmailVerificationCode(
            user_id=user.id,
            code=code,
            expires_at=datetime.now(UTC) + timedelta(minutes=settings.verification_code_expire_minutes),
            is_used=False,
        )
    )
    await send_verification_code(user.email, code)


def _decode_refresh_token(refresh_token: str) -> dict:
    try:
        payload = decode_token(refresh_token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Yangilash tokenining noto'g'ri.") from exc

    if payload.get("token_type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token turi noto'g'ri.")
    return payload
