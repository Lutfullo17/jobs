import asyncio
import logging
from socket import create_connection
from urllib.parse import urlparse

from app.core.config import settings
from app.tasks.email_tasks import send_email_now, send_email_task

logger = logging.getLogger("uvicorn.error")


async def send_email(to_email: str, subject: str, body: str) -> None:
    if settings.email_delivery_mode == "direct":
        await asyncio.to_thread(send_email_now, to_email, subject, body)
        return

    # HTTP request sekinlashmasligi uchun emailni Celery orqali yuboramiz.
    # Redis ishlamayotgan development holatida SMTP sozlangan bo'lsa to'g'ridan-to'g'ri yuboramiz.
    parsed = urlparse(settings.redis_url)
    redis_host = parsed.hostname or "localhost"
    redis_port = parsed.port or 6379
    try:
        with create_connection((redis_host, redis_port), timeout=0.3):
            pass
    except OSError:
        await asyncio.to_thread(send_email_now, to_email, subject, body)
        return

    try:
        send_email_task.delay(to_email, subject, body)
    except Exception:
        await asyncio.to_thread(send_email_now, to_email, subject, body)


async def send_verification_code(email: str, code: str) -> None:
    _print_code("VERIFICATION-CODE", email, code)
    subject = "Jobify - Email Verification Code"
    body = f"Sizning tasdiqlash kodingiz: {code}\nKod 10 daqiqa amal qiladi."
    await send_email(email, subject, body)


async def send_password_reset_code(email: str, code: str) -> None:
    _print_code("RESET-CODE", email, code)
    subject = "Jobify - Password Reset Code"
    body = f"Sizning parol tiklash kodingiz: {code}\nKod 10 daqiqa amal qiladi."
    await send_email(email, subject, body)


async def send_hr_registration_admin_notification(admin_email: str, hr_email: str, hr_user_id: int) -> None:
    subject = "Jobify - Yangi HR ro‘yxatdan o‘tdi"
    body = (
        f"Yangi HR akkaunti yaratildi.\n\n"
        f"HR email: {hr_email}\n"
        f"Foydalanuvchi ID: {hr_user_id}\n\n"
        f"Admin paneli orqali tasdiqlangandan keyin vakansiya joylash mumkin bo‘ladi."
    )
    await send_email(admin_email, subject, body)


def _print_code(label: str, email: str, code: str) -> None:
    message = f"[{label}] email={email} code={code}"
    print(message, flush=True)
    logger.warning(message)