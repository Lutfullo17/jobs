from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import require_approved_hr
from app.models.user import User

router = APIRouter(prefix="/api/vacancies", tags=["Vacancies"])


class VacancyCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=8000)


class VacancyCreateResponse(BaseModel):
    message: str
    title: str


@router.post("/", response_model=VacancyCreateResponse, status_code=201)
async def create_vacancy(
    payload: VacancyCreateRequest,
    _: User = Depends(require_approved_hr),
) -> VacancyCreateResponse:
    """HR admin tomonidan tasdiqlangachgina ishlaydi; keyinroq DB ga yozish qo‘shiladi."""
    return VacancyCreateResponse(
        message="Vakansiya qabul qilindi (hozircha demo javob).",
        title=payload.title,
    )
