import re
import unicodedata

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company, CompanyMember
from app.models.vacancy import Vacancy, VacancyStatus
from app.schemas.company import CompanyCreateBody, CompanyUpdateBody


def _slugify(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "-", text).strip("-") or "company"


async def create_company(db: AsyncSession, *, hr_user_id: int, payload: CompanyCreateBody) -> Company:
    slug = payload.slug.strip() if payload.slug else _slugify(payload.name)
    existing = await db.execute(select(Company).where(Company.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bunday slug mavjud.")
    company = Company(
        name=payload.name.strip(),
        slug=slug,
        logo_url=payload.logo_url,
        about=payload.about,
        website=payload.website,
        industry=payload.industry,
        company_size=payload.company_size,
        country=payload.country,
        city=payload.city,
        address=payload.address,
    )
    db.add(company)
    await db.flush()
    db.add(CompanyMember(company_id=company.id, user_id=hr_user_id, role="owner"))
    await db.commit()
    await db.refresh(company)
    return company


async def get_company_by_slug(db: AsyncSession, slug: str) -> Company | None:
    q = await db.execute(select(Company).where(Company.slug == slug))
    return q.scalar_one_or_none()


async def list_company_vacancies(db: AsyncSession, company_id: int) -> list[Vacancy]:
    q = await db.execute(
        select(Vacancy).where(
            Vacancy.company_id == company_id,
            Vacancy.is_deleted.is_(False),
            Vacancy.status == VacancyStatus.published,
        )
    )
    return list(q.scalars().all())


async def ensure_hr_member(db: AsyncSession, company_id: int, hr_user_id: int) -> Company:
    q = await db.execute(
        select(Company)
        .join(CompanyMember, CompanyMember.company_id == Company.id)
        .where(Company.id == company_id, CompanyMember.user_id == hr_user_id)
    )
    company = q.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kompaniyaga ruxsat yo'q.")
    return company


async def update_company(
    db: AsyncSession, company_id: int, hr_user_id: int, payload: CompanyUpdateBody
) -> Company:
    company = await ensure_hr_member(db, company_id, hr_user_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(company, k, v)
    await db.commit()
    await db.refresh(company)
    return company
