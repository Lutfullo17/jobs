import smtplib
from email.message import EmailMessage

from app.core.celery_app import celery_app
from app.core.config import settings


@celery_app.task(name="send_email_task", ignore_result=True)
def send_email_task(to_email: str, subject: str, body: str) -> None:
    send_email_now(to_email, subject, body)


def send_email_now(to_email: str, subject: str, body: str) -> None:
    # SMTP login bo'lmasa local development uchun faqat print qilamiz.
    if not settings.smtp_user or not settings.smtp_password:
        print(f"[EMAIL-DEV] To={to_email} | Subject={subject} | Body={body}")
        return

    message = EmailMessage()
    from_email = settings.smtp_user if str(settings.email_from) == "noreply@example.com" else str(settings.email_from)
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_use_starttls:
            server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)
