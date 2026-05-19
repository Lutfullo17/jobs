"""Bildirishnomalar, sevimlilar, saqlangan qidiruvlar, intervyular."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class NotificationType(str, enum.Enum):
    application_submitted = "application_submitted"
    application_viewed = "application_viewed"
    application_status_changed = "application_status_changed"
    new_message = "new_message"
    interview_scheduled = "interview_scheduled"
    hr_approved = "hr_approved"
    vacancy_expired = "vacancy_expired"


class InterviewFormat(str, enum.Enum):
    offline = "offline"
    google_meet = "google_meet"
    zoom = "zoom"
    phone = "phone"


class InterviewStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"
    declined = "declined"


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


class SavedVacancy(Base):
    __tablename__ = "saved_vacancies"
    __table_args__ = (UniqueConstraint("candidate_id", "vacancy_id", name="uq_saved_vacancy"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    vacancy_id: Mapped[int] = mapped_column(Integer, ForeignKey("vacancies.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    vacancy: Mapped["Vacancy"] = relationship("Vacancy")


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    filters_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vacancy_applications.id", ondelete="CASCADE"), index=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    format: Mapped[InterviewFormat] = mapped_column(
        SAEnum(InterviewFormat, native_enum=False, validate_strings=True), nullable=False
    )
    location_or_link: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[InterviewStatus] = mapped_column(
        SAEnum(InterviewStatus, native_enum=False, validate_strings=True),
        default=InterviewStatus.pending,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
