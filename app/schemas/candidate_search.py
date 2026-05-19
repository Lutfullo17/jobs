from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.vacancy import ApplicationStatus, EmploymentType, ExperienceLevel, WorkMode
from app.schemas.hr_vacancy import VacancyPublicListItem


class CandidateVacancyListItem(VacancyPublicListItem):
    """Vakansiya qidiruvi — nomzod uchun qo'shimcha flaglar."""

    already_applied: bool = False
    application_id: int | None = None
    application_status: ApplicationStatus | None = None


class CandidateApplicationListItem(BaseModel):
    id: int
    vacancy_id: int
    vacancy_title: str
    company_name: str
    location: str
    status: ApplicationStatus
    initial_message: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VacancyFilterOptionsOut(BaseModel):
    """Frontend select uchun mavjud filter qiymatlari."""

    employment_types: list[str]
    work_modes: list[str]
    experience_levels: list[str]
    application_statuses: list[str]
    vacancy_sort_options: list[str]
    application_sort_options: list[str]


class ApplicationFilterOptionsOut(BaseModel):
    statuses: list[str]
    employment_types: list[str]
    work_modes: list[str]
    sort_options: list[str]
