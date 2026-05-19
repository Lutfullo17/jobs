from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.candidate_profile import PreferredWorkMode


class ExperienceIn(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    position: str = Field(min_length=1, max_length=200)
    started_at: date | None = None
    ended_at: date | None = None
    is_current: bool = False
    description: str = ""


class EducationIn(BaseModel):
    institution: str = Field(min_length=1, max_length=255)
    degree: str = ""
    field_of_study: str = ""
    started_at: date | None = None
    ended_at: date | None = None


class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    level: str = ""


class LanguageIn(BaseModel):
    language: str = Field(min_length=1, max_length=80)
    level: str = ""


class CertificateIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    issuer: str = ""
    issued_at: date | None = None
    credential_url: str | None = None


class ProfileUpdateBody(BaseModel):
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=50)
    birth_date: date | None = None
    city: str | None = Field(None, max_length=120)
    country: str | None = Field(None, max_length=120)
    telegram: str | None = None
    linkedin: str | None = None
    github: str | None = None
    portfolio_url: str | None = None
    about_me: str | None = None
    expected_salary_from: int | None = Field(None, ge=0)
    expected_salary_to: int | None = Field(None, ge=0)
    currency: str | None = Field(None, max_length=10)
    preferred_work_mode: PreferredWorkMode | None = None
    preferred_employment_type: str | None = None
    profile_visible: bool | None = None


class ProfileFullUpdateBody(ProfileUpdateBody):
    experiences: list[ExperienceIn] | None = None
    educations: list[EducationIn] | None = None
    skills: list[SkillIn] | None = None
    languages: list[LanguageIn] | None = None
    certificates: list[CertificateIn] | None = None


class ExperienceOut(ExperienceIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class EducationOut(EducationIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class SkillOut(SkillIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class LanguageOut(LanguageIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class CertificateOut(CertificateIn):
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
