from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.platform import InterviewFormat, InterviewStatus, NotificationType
from app.models.vacancy import ApplicationStatus
from app.schemas.hr_vacancy import VacancyPublicListItem


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


class SavedSearchCreateBody(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    filters_json: str = Field(description="JSON filter parametrlari")


class SavedSearchOut(BaseModel):
    id: int
    name: str
    filters_json: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SavedVacancyOut(BaseModel):
    id: int
    vacancy_id: int
    created_at: datetime
    vacancy: VacancyPublicListItem | None = None

    model_config = ConfigDict(from_attributes=True)


class InterviewScheduleBody(BaseModel):
    scheduled_at: datetime
    format: InterviewFormat
    location_or_link: str = ""
    notes: str = ""


class InterviewOut(BaseModel):
    id: int
    application_id: int
    scheduled_at: datetime
    format: InterviewFormat
    location_or_link: str
    notes: str
    status: InterviewStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationStatusUpdateBody(BaseModel):
    status: ApplicationStatus
    hr_note: str | None = None
    internal_comment: str | None = None
    rating: int | None = Field(None, ge=1, le=5)
    rejection_reason: str | None = None


class PipelineStageCount(BaseModel):
    status: str
    count: int


class CandidateDashboardOut(BaseModel):
    applications_total: int
    applications_by_status: list[PipelineStageCount]
    favorites_count: int
    unread_notifications: int
    profile_completeness_percent: int
    saved_searches_count: int
