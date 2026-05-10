from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.vacancy import ApplicationStatus, EmploymentType, WorkMode


class HrStatusResponse(BaseModel):
    """HR o'zi admin tomonidan tasdiqlanganligini ko'radi."""

    hr_approved: bool
    can_post_vacancies: bool  # hozircha = hr_approved


class VacancyPublicListItem(BaseModel):
    id: int
    title: str
    company_name: str
    location: str
    employment_type: EmploymentType
    work_mode: WorkMode
    salary_from: int | None
    salary_to: int | None
    salary_currency: str
    salary_negotiable: bool
    expires_at: date | None
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
    company_name: str = Field(min_length=1, max_length=255, description="Kompaniya nomi")
    location: str = Field(min_length=1, max_length=255, description="Hudud / shahar")
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


class VacancyHrItem(BaseModel):
    id: int
    hr_id: int
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
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


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
    created_at: datetime


class ApplicationDetailOut(BaseModel):
    id: int
    vacancy_id: int
    vacancy_title: str
    candidate_id: int
    candidate_email: EmailStr
    status: ApplicationStatus
    initial_message: str
    created_at: datetime
    chat_messages: list[ChatMessageOut]


class RecruitmentActionResponse(BaseModel):
    application_id: int
    status: ApplicationStatus
    message: str


class RecruitmentChatBody(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


class RecruitmentChatResponse(BaseModel):
    message: str
