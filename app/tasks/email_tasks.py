import smtplib
from email.message import EmailMessage

from app.core.celery_app import celery_app
from app.core.config import settings


@celery_app.task(name="send_email_task", ignore_result=True)
def send_email_task(to_email: str, subject: str, body: str) -> None:
    print(f"\n{'='*60}")
    print(f"[EMAIL][CELERY] To:      {to_email}")
    print(f"[EMAIL][CELERY] Subject: {subject}")
    print(f"[EMAIL][CELERY] Body:    {body}")
    print(f"{'='*60}\n")

    if not settings.smtp_user or not settings.smtp_password:
        return

    message = EmailMessage()
    message["From"] = str(settings.email_from)
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_use_starttls:
            server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)
