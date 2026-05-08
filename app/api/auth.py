from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.core.redis_client import enforce_rate_limit
from app.core.config import settings
from app.models.user import User, UserRole
from app.schemas.auth import (
    AccessTokenResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserOut,
    VerifyEmailRequest,
)
from app.services.auth_service import (
    change_password,
    forgot_password,
    login_user,
    logout,
    logout_all_devices,
    refresh_access_token,
    register_user,
    resend_verification_code,
    reset_password,
    verify_email,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class MessageResponse(BaseModel):
    message: str


class ResendRequest(BaseModel):
    email: EmailStr


@router.post("/register/", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> RegisterResponse:
    user = await register_user(db, payload)
    return RegisterResponse(user=UserOut.model_validate(user), message="Email verification code sent.")


@router.post("/verify-email/", response_model=MessageResponse)
async def verify_email_endpoint(payload: VerifyEmailRequest, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    await verify_email(db, payload)
    return MessageResponse(message="Email verified successfully.")


@router.post("/resend-verification-code/", response_model=MessageResponse)
async def resend_verification_endpoint(
    payload: ResendRequest, request: Request, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"rate:resend:{client_ip}:{payload.email}"
    allowed = await enforce_rate_limit(
        rate_key,
        settings.rate_limit_resend_limit,
        settings.rate_limit_resend_window_seconds,
    )
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests. Try again later.")
    await resend_verification_code(db, payload.email)
    return MessageResponse(message="Verification code sent.")


@router.post("/login/", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"rate:login:{client_ip}:{payload.email}"
    allowed = await enforce_rate_limit(
        rate_key,
        settings.rate_limit_login_limit,
        settings.rate_limit_login_window_seconds,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )

    access_token, refresh_token, user = await login_user(
        db=db,
        payload=payload,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserOut.model_validate(user),
    )


@router.post("/refresh/", response_model=AccessTokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> AccessTokenResponse:
    new_access, new_refresh = await refresh_access_token(db, payload.refresh_token)
    return AccessTokenResponse(access_token=new_access, refresh_token=new_refresh)


@router.post("/logout/", response_model=MessageResponse)
async def logout_endpoint(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    await logout(db, payload.refresh_token)
    return MessageResponse(message="Logged out successfully.")


@router.post("/logout-all/", response_model=MessageResponse)
async def logout_all_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    revoked_count = await logout_all_devices(db, current_user.id)
    return MessageResponse(message=f"All devices logged out. Revoked tokens: {revoked_count}")


@router.get("/me/", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.get("/admin-only/", response_model=MessageResponse)
async def admin_only(_: User = Depends(require_role(UserRole.admin))) -> MessageResponse:
    return MessageResponse(message="Welcome Admin. You can access this endpoint.")


@router.get("/hr-only/", response_model=MessageResponse)
async def hr_only(_: User = Depends(require_role(UserRole.hr))) -> MessageResponse:
    return MessageResponse(message="Welcome HR. You can access this endpoint.")


@router.get("/candidate-only/", response_model=MessageResponse)
async def candidate_only(_: User = Depends(require_role(UserRole.candidate))) -> MessageResponse:
    return MessageResponse(message="Welcome Candidate. You can access this endpoint.")


@router.post("/change-password/", response_model=MessageResponse)
async def change_password_endpoint(
    payload: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    await change_password(db, current_user, payload)
    return MessageResponse(message="Password changed successfully.")


@router.post("/forgot-password/", response_model=MessageResponse)
async def forgot_password_endpoint(
    payload: ForgotPasswordRequest, request: Request, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"rate:forgot:{client_ip}:{payload.email}"
    allowed = await enforce_rate_limit(
        rate_key,
        settings.rate_limit_forgot_limit,
        settings.rate_limit_forgot_window_seconds,
    )
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests. Try again later.")
    await forgot_password(db, payload)
    return MessageResponse(message="If this email exists, reset code has been sent.")


@router.post("/reset-password/", response_model=MessageResponse)
async def reset_password_endpoint(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    await reset_password(db, payload)
    return MessageResponse(message="Password reset successfully.")
