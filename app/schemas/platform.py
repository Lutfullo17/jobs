from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.platform import NotificationType


class NotificationOut(BaseModel):
    id: int
    type: NotificationType
    title: str
    body: str
    is_read: bool
    related_entity_type: str | None
    related_entity_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PipelineStageCount(BaseModel):
    status: str
    count: int


class CandidateDashboardOut(BaseModel):
    applications_total: int
    applications_by_status: list[PipelineStageCount]
    unread_notifications: int
    profile_completeness_percent: int
