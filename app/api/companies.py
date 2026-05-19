"""Kompaniyalar (employer profile)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_approved_hr
from app.models.user import User
from app.schemas.company import CompanyCreateBody, CompanyOut, CompanyPublicOut, CompanyUpdateBody
from app.schemas.hr_vacancy import VacancyPublicListItem
from app.services.company_service import (
    create_company,
    get_company_by_slug,
    list_company_vacancies,
    update_company,
)

router = APIRouter(prefix="/api/companies", tags=["Kompaniyalar"])


@router.post("/", response_model=CompanyOut, status_code=201)
async def create_company_endpoint(
    payload: CompanyCreateBody,
    db: AsyncSession = Depends(get_db),
    hr: User = Depends(require_approved_hr),
) -> CompanyOut:
    company = await create_company(db, hr_user_id=hr.id, payload=payload)
    return CompanyOut.model_validate(company)


@router.get("/{slug}/", response_model=CompanyPublicOut)
async def company_public_page(slug: str, db: AsyncSession = Depends(get_db)) -> CompanyPublicOut:
    company = await get_company_by_slug(db, slug)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kompaniya topilmadi.")
    return CompanyPublicOut.model_validate(company)


@router.get("/{slug}/vacancies/", response_model=list[VacancyPublicListItem])
async def company_vacancies(slug: str, db: AsyncSession = Depends(get_db)) -> list[VacancyPublicListItem]:
    company = await get_company_by_slug(db, slug)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kompaniya topilmadi.")
    rows = await list_company_vacancies(db, company.id)
    return [VacancyPublicListItem.model_validate(v) for v in rows]


@router.patch("/{company_id}/", response_model=CompanyOut)
async def patch_company(
    company_id: int,
    payload: CompanyUpdateBody,
    db: AsyncSession = Depends(get_db),
    hr: User = Depends(require_approved_hr),
) -> CompanyOut:
    company = await update_company(db, company_id, hr.id, payload)
    return CompanyOut.model_validate(company)
