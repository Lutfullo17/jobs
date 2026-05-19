from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.vacancy import ApplicationStatus, EmploymentType, ExperienceLevel, VacancyStatus, WorkMode


class HrStatusResponse(BaseModel):
    """HR o'zi admin tomonidan tasdiqlanganligini ko'radi."""

    hr_approved: bool
    can_post_vacancies: bool  # hozircha = hr_approved


class VacancyPublicListItem(BaseModel):
    id: int
    title: str
    company_name: str
    company_id: int | None = None
    location: str
    employment_type: EmploymentType
    work_mode: WorkMode
    experience_level: ExperienceLevel | None = None
    industry: str = ""
    salary_from: int | None
    salary_to: int | None
    salary_currency: str
    salary_negotiable: bool
    is_remote_worldwide: bool = False
    expires_at: date | None
    published_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VacancyPublicDetail(BaseModel):
    id: int
    title: str
    description: str
    company_name: str
    location: str
    employment_type: EmploymentType
    work_mode: WorkMode
    salary_from: int | None
    salary_to: int | None
    salary_currency: str
    salary_negotiable: bool
    responsibilities: str
    requirements: str
    benefits: str
    experience_note: str
    education_note: str
    contact_phone: str | None
    expires_at: date | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VacancyCreateBody(BaseModel):
    title: str = Field(min_length=1, max_length=200, description="Lavozim nomi")
    description: str = Field(min_length=1, max_length=16000, description="Kompaniya / lavozim haqida qisqa tavsif")
    company_id: int | None = Field(None, description="Kompaniya ID (ixtiyoriy)")
    company_name: str = Field(min_length=1, max_length=255, description="Kompaniya nomi")
    location: str = Field(min_length=1, max_length=255, description="Hudud / shahar")
    experience_level: ExperienceLevel | None = None
    industry: str = ""
    skills_required: str = ""
    headcount: int = Field(default=1, ge=1)
    screening_questions: str = ""
    is_remote_worldwide: bool = False
    employment_type: EmploymentType = Field(description="Ish grafiki turi")
    work_mode: WorkMode = Field(description="Ofis, masofadan yoki aralash")
    responsibilities: str = Field(min_length=1, max_length=32000, description="Asosiy vazifalar")
    requirements: str = Field(min_length=1, max_length=32000, description="Talablar (skills, boshqalar)")
    benefits: str = Field(default="", max_length=16000, description="Bonuslar va imtiyozlar (ixtiyoriy)")
    salary_from: int | None = Field(default=None, ge=0, description="Masalan oyiga UZSdan")
    salary_to: int | None = Field(default=None, ge=0, description="Masalan oyiga UZSgacha")
    salary_currency: str = Field(default="UZS", min_length=1, max_length=10)
    salary_negotiable: bool = Field(default=True, description="Kelishilish mumkin")
    experience_note: str = Field(default="", max_length=500, description="Masalan \"2–3 yil\"")
    education_note: str = Field(default="", max_length=255, description="Masalan \"Oliy / IT\"")
    contact_phone: str | None = Field(default=None, max_length=50)
    expires_at: date | None = Field(default=None, description="E'lon aktiv bo'ladigan oxirgi sana")

    @model_validator(mode="after")
    def check_salary_range(self) -> "VacancyCreateBody":
        a, b = self.salary_from, self.salary_to
        if a is not None and b is not None and a > b:
            raise ValueError("salary_from salary_to dan katta bo'lmasligi kerak.")
        return self


class VacancyUpdateBody(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1, max_length=16000)
    company_id: int | None = None
    company_name: str | None = Field(None, max_length=255)
    location: str | None = Field(None, max_length=255)
    employment_type: EmploymentType | None = None
    work_mode: WorkMode | None = None
    experience_level: ExperienceLevel | None = None
    industry: str | None = None
    skills_required: str | None = None
    headcount: int | None = Field(None, ge=1)
    screening_questions: str | None = None
    is_remote_worldwide: bool | None = None
    responsibilities: str | None = None
    requirements: str | None = None
    benefits: str | None = None
    salary_from: int | None = Field(None, ge=0)
    salary_to: int | None = Field(None, ge=0)
    salary_currency: str | None = None
    salary_negotiable: bool | None = None
    experience_note: str | None = None
    education_note: str | None = None
    contact_phone: str | None = None
    expires_at: date | None = None


class VacancyHrItem(BaseModel):
    id: int
    hr_id: int
    company_id: int | None = None
    status: VacancyStatus
    title: str
    description: str
    company_name: str
    location: str
    experience_level: ExperienceLevel | None = None
    industry: str = ""
    skills_required: str = ""
    headcount: int = 1
    is_remote_worldwide: bool = False
    employment_type: EmploymentType
    work_mode: WorkMode
    salary_from: int | None
    salary_to: int | None
    salary_currency: str
    salary_negotiable: bool
    responsibilities: str
    requirements: str
    benefits: str
    experience_note: str
    education_note: str
    contact_phone: str | None
    expires_at: date | None
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VacancyActionResponse(BaseModel):
    id: int
    status: VacancyStatus
    message: str


class VacancyDeletedResponse(BaseModel):
    message: str


class ApplyToVacancyBody(BaseModel):
    """Nomzod vakansiyaga faqat bir marta yuboradigan asosiy xabar."""

    message: str = Field(min_length=1, max_length=8000)


class ApplyToVacancyResponse(BaseModel):
    application_id: int
    vacancy_id: int
    status: ApplicationStatus
    message: str


class ChatMessageOut(BaseModel):
    id: int
    sender_id: int
    body: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationHrListOut(BaseModel):
    id: int
    vacancy_id: int
    vacancy_title: str
    candidate_id: int
    candidate_email: EmailStr
    status: ApplicationStatus
    initial_message: str
    hr_note: str = ""
    rating: int | None = None
    rejection_reason: str | None = None
    created_at: datetime
    resume_download_url: str | None = None


class ApplicationDetailOut(BaseModel):
    id: int
    vacancy_id: int
    vacancy_title: str
    candidate_id: int
    candidate_email: EmailStr
    status: ApplicationStatus
    initial_message: str
    hr_note: str = ""
    internal_comment: str = ""
    rating: int | None = None
    rejection_reason: str | None = None
    created_at: datetime
    resume_download_url: str | None = None
    chat_messages: list[ChatMessageOut]


class RecruitmentActionResponse(BaseModel):
    application_id: int
    status: ApplicationStatus
    message: str


class RecruitmentChatBody(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


class RecruitmentChatResponse(BaseModel):
    message: str
