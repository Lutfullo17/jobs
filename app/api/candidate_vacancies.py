"""
Nomzod: vakansiya qidiruvi va filterlar (autentifikatsiya talab qilinadi).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_candidate
from app.models.user import User
from app.models.vacancy import ApplicationStatus, EmploymentType, ExperienceLevel, WorkMode
from app.schemas.candidate_search import CandidateVacancyListItem, VacancyFilterOptionsOut
from app.schemas.common import PaginatedResponse, paginate
from app.services.vacancy_application_service import (
    get_candidate_vacancy_meta,
    list_active_vacancies,
)

router = APIRouter(prefix="/api/candidate/vacancies", tags=["Nomzod — vakansiya qidiruv"])


@router.get("/filters/", response_model=VacancyFilterOptionsOut)
async def vacancy_filter_options() -> VacancyFilterOptionsOut:
    return VacancyFilterOptionsOut(
        employment_types=[e.value for e in EmploymentType],
        work_modes=[w.value for w in WorkMode],
        experience_levels=[e.value for e in ExperienceLevel],
        application_statuses=[s.value for s in ApplicationStatus],
        vacancy_sort_options=["date_desc", "salary_desc", "relevance"],
        application_sort_options=["date_desc", "date_asc", "status"],
    )


@router.get("/", response_model=PaginatedResponse[CandidateVacancyListItem])
async def search_vacancies_for_candidate(
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
    q: str | None = Query(None, description="Lavozim / tavsif bo'yicha qidiruv"),
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
    exclude_applied: bool = Query(False, description="Murojaat qilgan vakansiyalarni yashirish"),
    favorites_only: bool = Query(False, description="Faqat sevimlilar"),
    sort_by: str = Query("date_desc", pattern="^(date_desc|salary_desc|relevance)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[CandidateVacancyListItem]:
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
        candidate_id=candidate.id,
        exclude_applied=exclude_applied,
        favorites_only=favorites_only,
    )
    ids = [v.id for v in rows]
    applied_ids, saved_ids, app_map = await get_candidate_vacancy_meta(db, candidate.id, ids)

    items: list[CandidateVacancyListItem] = []
    for v in rows:
        app = app_map.get(v.id)
        item = CandidateVacancyListItem.model_validate(v)
        item.already_applied = v.id in applied_ids
        item.is_saved = v.id in saved_ids
        if app:
            item.application_id = app.id
            item.application_status = app.status
        items.append(item)

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=paginate(total, page, page_size),
    )
