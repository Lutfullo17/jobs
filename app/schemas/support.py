"""Pydantic sxemalar: support thread va xabarlar API javoblari."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.support import SupportThreadStatus


class SupportMessageOut(BaseModel):
    id: int
    sender_id: int
    body: str
    created_at: datetime

    class Config:
        from_attributes = True


class SupportThreadCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=8000)


class SupportReplyBody(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


class SupportThreadListItem(BaseModel):
    id: int
    subject: str
    status: SupportThreadStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupportThreadDetail(BaseModel):
    id: int
    subject: str
    status: SupportThreadStatus
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    messages: list[SupportMessageOut]

    class Config:
        from_attributes = True


class SupportReplyResponse(BaseModel):
    message: str
