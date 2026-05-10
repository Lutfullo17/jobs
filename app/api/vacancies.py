"""
Ochiq vakansiya ro'yxati (login shart emas).

Nomzod murojaati: `POST .../apply/` — autentifikatsiya kerak (candidate token).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_candidate
from app.models.user import User
from app.schemas.hr_vacancy import (
    ApplyToVacancyBody,
    ApplyToVacancyResponse,
    VacancyPublicDetail,
    VacancyPublicListItem,
)
from app.services.vacancy_application_service import (
    apply_to_vacancy,
    get_active_vacancy,
    list_active_vacancies,
)

router = APIRouter(prefix="/api/vacancies", tags=["Vakansiyalar — ochiq"])


@router.get("/", response_model=list[VacancyPublicListItem])
async def list_open_vacancies(db: AsyncSession = Depends(get_db)) -> list[VacancyPublicListItem]:
    rows = await list_active_vacancies(db)
    return [VacancyPublicListItem.model_validate(r) for r in rows]


@router.get("/{vacancy_id}/", response_model=VacancyPublicDetail)
async def get_open_vacancy(vacancy_id: int, db: AsyncSession = Depends(get_db)) -> VacancyPublicDetail:
    v = await get_active_vacancy(db, vacancy_id)
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vakansiya topilmadi.")
    return VacancyPublicDetail.model_validate(v)


@router.post("/{vacancy_id}/apply/", response_model=ApplyToVacancyResponse, status_code=201)
async def apply_once(
    vacancy_id: int,
    payload: ApplyToVacancyBody,
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> ApplyToVacancyResponse:
    """Bir nomzod — bir vakansiyaga bir marta."""
    row = await apply_to_vacancy(db, vacancy_id=vacancy_id, candidate=candidate, message=payload.message)
    return ApplyToVacancyResponse(
        application_id=row.id,
        vacancy_id=row.vacancy_id,
        status=row.status,
        message="Murojaat qabul qilindi. HR javobini kuting.",
    )
