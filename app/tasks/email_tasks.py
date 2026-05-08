import smtplib
from email.message import EmailMessage

from app.core.celery_app import celery_app
from app.core.config import settings


@celery_app.task(name="send_email_task")
def send_email_task(to_email: str, subject: str, body: str) -> None:
    # SMTP login bo'lmasa local development uchun faqat print qilamiz.
    if not settings.smtp_user or not settings.smtp_password:
        print(f"[EMAIL-DEV][CELERY] To={to_email} | Subject={subject} | Body={body}")
        return

    message = EmailMessage()
    message["From"] = str(settings.email_from)
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    smtp_client = smtplib.SMTP_SSL if settings.smtp_use_tls else smtplib.SMTP
    with smtp_client(settings.smtp_host, settings.smtp_port) as server:
        if not settings.smtp_use_tls and settings.smtp_use_starttls:
            server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)
