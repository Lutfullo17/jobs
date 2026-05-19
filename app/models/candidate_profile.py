"""Nomzod profili va structured resume bo'limlari."""

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PreferredWorkMode(str, enum.Enum):
    office = "office"
    remote = "remote"
    hybrid = "hybrid"
    any = "any"


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    city: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    country: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    telegram: Mapped[str | None] = mapped_column(String(120), nullable=True)
    linkedin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github: Mapped[str | None] = mapped_column(String(255), nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    about_me: Mapped[str] = mapped_column(Text, default="", nullable=False)
    expected_salary_from: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_salary_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="UZS", nullable=False)
    preferred_work_mode: Mapped[PreferredWorkMode] = mapped_column(
        SAEnum(PreferredWorkMode, native_enum=False, validate_strings=True),
        default=PreferredWorkMode.any,
        nullable=False,
    )
    preferred_employment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    profile_visible: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    experiences: Mapped[list["CandidateExperience"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    educations: Mapped[list["CandidateEducation"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    skills: Mapped[list["CandidateSkill"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    languages: Mapped[list["CandidateLanguage"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    certificates: Mapped[list["CandidateCertificate"]] = relationship(back_populates="profile", cascade="all, delete-orphan")


class CandidateExperience(Base):
    __tablename__ = "candidate_experiences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str] = mapped_column(String(200), nullable=False)
    started_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    ended_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(default=False, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    profile: Mapped["CandidateProfile"] = relationship(back_populates="experiences")


class CandidateEducation(Base):
    __tablename__ = "candidate_educations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True)
    institution: Mapped[str] = mapped_column(String(255), nullable=False)
    degree: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    field_of_study: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    started_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    ended_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    profile: Mapped["CandidateProfile"] = relationship(back_populates="educations")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    level: Mapped[str] = mapped_column(String(50), default="", nullable=False)

    profile: Mapped["CandidateProfile"] = relationship(back_populates="skills")


class CandidateLanguage(Base):
    __tablename__ = "candidate_languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True)
    language: Mapped[str] = mapped_column(String(80), nullable=False)
    level: Mapped[str] = mapped_column(String(50), default="", nullable=False)

    profile: Mapped["CandidateProfile"] = relationship(back_populates="languages")


class CandidateCertificate(Base):
    __tablename__ = "candidate_certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    issued_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    credential_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    profile: Mapped["CandidateProfile"] = relationship(back_populates="certificates")
