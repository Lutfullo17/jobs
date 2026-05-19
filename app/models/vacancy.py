"""
Vakansiyalar va nomzod murojaatlari.
"""

import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.user import User


class ApplicationStatus(str, enum.Enum):
    # Legacy (migratsiyadan qolgan)
    pending = "pending"
    chat_open = "chat_open"
    rejected = "rejected"
    # Pipeline
    applied = "applied"
    viewed = "viewed"
    shortlisted = "shortlisted"
    screening = "screening"
    interview_scheduled = "interview_scheduled"
    interviewed = "interviewed"
    test_task = "test_task"
    offer_sent = "offer_sent"
    hired = "hired"
    withdrawn = "withdrawn"


# Suhbat ochiq bo'ladigan statuslar
CHAT_ACTIVE_STATUSES = frozenset(
    {
        ApplicationStatus.chat_open,
        ApplicationStatus.screening,
        ApplicationStatus.shortlisted,
        ApplicationStatus.interview_scheduled,
        ApplicationStatus.interviewed,
        ApplicationStatus.test_task,
        ApplicationStatus.offer_sent,
    }
)


class VacancyStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"
    closed = "closed"
    on_moderation = "on_moderation"
    rejected_by_admin = "rejected_by_admin"


class ExperienceLevel(str, enum.Enum):
    intern = "intern"
    junior = "junior"
    middle = "middle"
    senior = "senior"
    lead = "lead"


class EmploymentType(str, enum.Enum):
    full_time = "full_time"
    part_time = "part_time"
    contract = "contract"
    internship = "internship"


class WorkMode(str, enum.Enum):
    office = "office"
    remote = "remote"
    hybrid = "hybrid"


class Vacancy(Base):
    __tablename__ = "vacancies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hr_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    location: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    employment_type: Mapped[EmploymentType] = mapped_column(
        SAEnum(EmploymentType, native_enum=False, validate_strings=True),
        nullable=False,
        default=EmploymentType.full_time,
    )
    work_mode: Mapped[WorkMode] = mapped_column(
        SAEnum(WorkMode, native_enum=False, validate_strings=True),
        nullable=False,
        default=WorkMode.office,
    )
    status: Mapped[VacancyStatus] = mapped_column(
        SAEnum(VacancyStatus, native_enum=False, validate_strings=True),
        nullable=False,
        default=VacancyStatus.draft,
    )
    experience_level: Mapped[ExperienceLevel | None] = mapped_column(
        SAEnum(ExperienceLevel, native_enum=False, validate_strings=True),
        nullable=True,
    )
    industry: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    skills_required: Mapped[str] = mapped_column(Text, default="", nullable=False)
    headcount: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    screening_questions: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_remote_worldwide: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    salary_from: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(10), default="UZS", nullable=False)
    salary_negotiable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    responsibilities: Mapped[str] = mapped_column(Text, default="", nullable=False)
    requirements: Mapped[str] = mapped_column(Text, default="", nullable=False)
    benefits: Mapped[str] = mapped_column(Text, default="", nullable=False)
    experience_note: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    education_note: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    expires_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    company: Mapped["Company | None"] = relationship("Company", back_populates="vacancies")
    applications: Mapped[list["VacancyApplication"]] = relationship(
        "VacancyApplication", back_populates="vacancy"
    )


class VacancyApplication(Base):
    __tablename__ = "vacancy_applications"
    __table_args__ = (UniqueConstraint("vacancy_id", "candidate_id", name="uq_vacancy_candidate"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vacancy_id: Mapped[int] = mapped_column(Integer, ForeignKey("vacancies.id", ondelete="CASCADE"), index=True)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    initial_message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus, native_enum=False, validate_strings=True),
        nullable=False,
        default=ApplicationStatus.applied,
    )
    hr_note: Mapped[str] = mapped_column(Text, default="", nullable=False)
    internal_comment: Mapped[str] = mapped_column(Text, default="", nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    vacancy: Mapped["Vacancy"] = relationship("Vacancy", back_populates="applications")
    candidate: Mapped[User] = relationship(foreign_keys=[candidate_id])
    chat_messages: Mapped[list["ApplicationMessage"]] = relationship(
        "ApplicationMessage", back_populates="application"
    )


class ApplicationMessage(Base):
    __tablename__ = "application_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vacancy_applications.id", ondelete="CASCADE"), index=True
    )
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["VacancyApplication"] = relationship("VacancyApplication", back_populates="chat_messages")
