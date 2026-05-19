import sys
from socket import create_connection
from urllib.parse import urlparse

from app.core.config import settings
from app.tasks.email_tasks import send_email_task


def _emit_console_line(line: str) -> None:
    # stderr: IDE/Docker terminalda darhol ko‘rinadi (stdout ba’zan boshqa yo‘naladi).
    sys.stderr.write(line + "\n")
    sys.stderr.flush()


async def send_email(to_email: str, subject: str, body: str) -> None:
    # SMTP yo'q bo'lsa Celery worker talab etilmaydi; aks holda kod faqat worker terminalida
    # chiqardi va uvicorn oynasida "kod kelmayapti" bo'lib qolardi.
    if not settings.smtp_user or not settings.smtp_password:
        _emit_console_line(f"[EMAIL-DEV] To={to_email} | Subject={subject} | Body={body}")
        return

    # HTTP request sekinlashmasligi uchun emailni Celery orqali yuboramiz.
    # Redis/Celery ishlamayotgan development holatida auth endpointlar yiqilmasligi uchun fail-open.
    parsed = urlparse(settings.redis_url)
    redis_host = parsed.hostname or "localhost"
    redis_port = parsed.port or 6379
    try:
        with create_connection((redis_host, redis_port), timeout=0.3):
            pass
    except OSError:
        _emit_console_line(f"[EMAIL-FALLBACK] To={to_email} | Subject={subject} | Body={body}")
        return

    try:
        send_email_task.delay(to_email, subject, body)
    except Exception:
        _emit_console_line(f"[EMAIL-FALLBACK] To={to_email} | Subject={subject} | Body={body}")


def _minutes_label(minutes: int) -> str:
    return f"{minutes} daqiqa"


async def send_verification_code(email: str, code: str) -> None:
    subject = "Jobify - Email Verification Code"
    mins = settings.verification_code_expire_minutes
    body = f"Sizning tasdiqlash kodingiz: {code}\nKod {_minutes_label(mins)} amal qiladi."
    # Email yuborilishi bilan bog'liq emas — kod har doim shu jarayon terminaliga chiqadi
    _emit_console_line(f"[VERIFICATION-CODE] email={email} code={code}")
    await send_email(email, subject, body)


async def send_password_reset_code(email: str, code: str) -> None:
    subject = "Jobify - Password Reset Code"
    mins = settings.reset_code_expire_minutes
    body = f"Sizning parol tiklash kodingiz: {code}\nKod {_minutes_label(mins)} amal qiladi."
    _emit_console_line(f"[RESET-CODE] email={email} code={code}")
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




    