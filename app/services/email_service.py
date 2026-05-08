from app.tasks.email_tasks import send_email_task


async def send_email(to_email: str, subject: str, body: str) -> None:
    # HTTP request sekinlashmasligi uchun emailni Celery orqali yuboramiz.
    send_email_task.delay(to_email, subject, body)


async def send_verification_code(email: str, code: str) -> None:
    subject = "Jobify - Email Verification Code"
    body = f"Sizning tasdiqlash kodingiz: {code}\nKod 10 daqiqa amal qiladi."
    await send_email(email, subject, body)


async def send_password_reset_code(email: str, code: str) -> None:
    subject = "Jobify - Password Reset Code"
    body = f"Sizning parol tiklash kodingiz: {code}\nKod 10 daqiqa amal qiladi."
    await send_email(email, subject, body)
