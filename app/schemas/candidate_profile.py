from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.candidate_profile import PreferredWorkMode


class ExperienceOut(BaseModel):
    company_name: str
    position: str
    started_at: date | None = None
    ended_at: date | None = None
    is_current: bool = False
    description: str = ""
    id: int
    model_config = ConfigDict(from_attributes=True)


class EducationOut(BaseModel):
    institution: str
    degree: str = ""
    field_of_study: str = ""
    started_at: date | None = None
    ended_at: date | None = None
    id: int
    model_config = ConfigDict(from_attributes=True)


class SkillOut(BaseModel):
    name: str
    level: str = ""
    id: int
    model_config = ConfigDict(from_attributes=True)


class LanguageOut(BaseModel):
    language: str
    level: str = ""
    id: int
    model_config = ConfigDict(from_attributes=True)


class CertificateOut(BaseModel):
    title: str
    issuer: str = ""
    issued_at: date | None = None
    credential_url: str | None = None
    id: int
    model_config = ConfigDict(from_attributes=True)


class CandidateProfileOut(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    phone: str | None
    birth_date: date | None
    city: str
    country: str
    telegram: str | None
    linkedin: str | None
    github: str | None
    portfolio_url: str | None
    about_me: str
    expected_salary_from: int | None
    expected_salary_to: int | None
    currency: str
    preferred_work_mode: PreferredWorkMode
    preferred_employment_type: str | None
    profile_visible: bool
    completeness_percent: int = 0
    experiences: list[ExperienceOut] = []
    educations: list[EducationOut] = []
    skills: list[SkillOut] = []
    languages: list[LanguageOut] = []
    certificates: list[CertificateOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
