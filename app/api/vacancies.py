"""
Ochiq vakansiya ro'yxati (login shart emas).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_candidate
from app.models.user import User
from app.models.vacancy import EmploymentType, ExperienceLevel, WorkMode
from app.schemas.common import PaginatedResponse, paginate
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


@router.get("/", response_model=PaginatedResponse[VacancyPublicListItem])
async def list_open_vacancies(
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(None),
    location: str | None = Query(None),
    company_name: str | None = Query(None),
    employment_type: EmploymentType | None = Query(None),
    work_mode: WorkMode | None = Query(None),
    experience_level: ExperienceLevel | None = Query(None),
    industry: str | None = Query(None),
    skill: str | None = Query(None),
    remote_only: bool | None = Query(None),
    verified_company_only: bool | None = Query(None),
    posted_within_days: int | None = Query(None, ge=1, le=30),
    salary_from: int | None = Query(None, ge=0),
    salary_to: int | None = Query(None, ge=0),
    salary_currency: str | None = Query(None),
    salary_negotiable: bool | None = Query(None),
    sort_by: str = Query("date_desc", pattern="^(date_desc|salary_desc|relevance)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[VacancyPublicListItem]:
    rows, total = await list_active_vacancies(
        db,
        q=q,
        location=location,
        company_name=company_name,
        employment_type=employment_type,
        work_mode=work_mode,
        experience_level=experience_level,
        industry=industry,
        skill=skill,
        remote_only=remote_only,
        verified_company_only=verified_company_only,
        posted_within_days=posted_within_days,
        salary_from=salary_from,
        salary_to=salary_to,
        salary_currency=salary_currency,
        salary_negotiable=salary_negotiable,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[VacancyPublicListItem.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=paginate(total, page, page_size),
    )


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
    row = await apply_to_vacancy(db, vacancy_id=vacancy_id, candidate=candidate, message=payload.message)
    return ApplyToVacancyResponse(
        application_id=row.id,
        vacancy_id=row.vacancy_id,
        status=row.status,
        message="Murojaat qabul qilindi. HR javobini kuting.",
    )
