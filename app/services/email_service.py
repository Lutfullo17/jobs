from socket import create_connection
from urllib.parse import urlparse

from app.core.config import settings
from app.tasks.email_tasks import send_email_task


async def send_email(to_email: str, subject: str, body: str) -> None:
    # HTTP request sekinlashmasligi uchun emailni Celery orqali yuboramiz.
    # Redis/Celery ishlamayotgan development holatida auth endpointlar yiqilmasligi uchun fail-open.
    parsed = urlparse(settings.redis_url)
    redis_host = parsed.hostname or "localhost"
    redis_port = parsed.port or 6379
    try:
        with create_connection((redis_host, redis_port), timeout=0.3):
            pass
    except OSError:
        print(f"[EMAIL-FALLBACK] To={to_email} | Subject={subject} | Body={body}")
        return

    try:
        send_email_task.delay(to_email, subject, body)
    except Exception:
        print(f"[EMAIL-FALLBACK] To={to_email} | Subject={subject} | Body={body}")


async def send_verification_code(email: str, code: str) -> None:
    subject = "Jobify - Email Verification Code"
    body = f"Sizning tasdiqlash kodingiz: {code}\nKod 10 daqiqa amal qiladi."
    await send_email(email, subject, body)


async def send_password_reset_code(email: str, code: str) -> None:
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




    