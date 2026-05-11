from typing import Literal

from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Jobify Auth API"
    debug: bool = True

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/jobify"

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: EmailStr = "noreply@example.com"
    smtp_use_tls: bool = False
    smtp_use_starttls: bool = True
    email_delivery_mode: Literal["celery", "direct"] = "celery"

    redis_url: str = "redis://localhost:6379/0"
    verification_code_expire_minutes: int = 10
    reset_code_expire_minutes: int = 10
    rate_limit_login_limit: int = 5
    rate_limit_login_window_seconds: int = 60
    rate_limit_resend_limit: int = 1
    rate_limit_resend_window_seconds: int = 60
    rate_limit_forgot_limit: int = 3
    rate_limit_forgot_window_seconds: int = 300


settings = Settings()
