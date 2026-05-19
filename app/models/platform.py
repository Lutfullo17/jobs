"""Bildirishnomalar."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NotificationType(str, enum.Enum):
    application_submitted = "application_submitted"
    application_viewed = "application_viewed"
    application_status_changed = "application_status_changed"
    new_message = "new_message"
    interview_scheduled = "interview_scheduled"
    hr_approved = "hr_approved"
    vacancy_expired = "vacancy_expired"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[NotificationType] = mapped_column(
        SAEnum(NotificationType, native_enum=False, validate_strings=True), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    related_entity_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    related_entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
