"""
Admin bilan yozishmalar (support ticket).

G'oya:
- HR yoki nomzod "mavzu" ochadi va birinchi xabarni yozadi (SupportThread + SupportMessage).
- Admin barcha mavzularni ko'radi va javob beradi (yana SupportMessage).
- Mavzu ochgan faqat o'z thread'larini ko'radi; admin hammasini ko'radi.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SupportThreadStatus(str, enum.Enum):
    open = "open"
    closed = "closed"


class SupportThread(Base):
    __tablename__ = "support_threads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Kim murojaat qilgan (HR yoki candidate)
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[SupportThreadStatus] = mapped_column(
        SAEnum(SupportThreadStatus),
        nullable=False,
        default=SupportThreadStatus.open,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["SupportMessage"]] = relationship("SupportMessage", back_populates="thread")


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    thread_id: Mapped[int] = mapped_column(Integer, ForeignKey("support_threads.id", ondelete="CASCADE"))
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    thread: Mapped["SupportThread"] = relationship("SupportThread", back_populates="messages")
