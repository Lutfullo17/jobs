"""Kompaniya va HR a'zoligi."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    about: Mapped[str] = mapped_column(Text, default="", nullable=False)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    industry: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    company_size: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    country: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    city: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    address: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    members: Mapped[list["CompanyMember"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    vacancies: Mapped[list["Vacancy"]] = relationship("Vacancy", back_populates="company")


class CompanyMember(Base):
    __tablename__ = "company_members"
    __table_args__ = (UniqueConstraint("company_id", "user_id", name="uq_company_member"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(50), default="hr", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="members")
