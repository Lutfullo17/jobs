from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import json

from app.models.platform import SavedSearch, SavedVacancy
from app.models.vacancy import EmploymentType, ExperienceLevel, Vacancy, WorkMode
from app.services.vacancy_application_service import get_active_vacancy, list_active_vacancies


async def add_favorite(db: AsyncSession, candidate_id: int, vacancy_id: int) -> SavedVacancy:
    v = await get_active_vacancy(db, vacancy_id)
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vakansiya topilmadi.")
    row = SavedVacancy(candidate_id=candidate_id, vacancy_id=vacancy_id)
    db.add(row)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Allaqachon saqlangan.") from exc
    await db.refresh(row)
    return row


async def remove_favorite(db: AsyncSession, candidate_id: int, vacancy_id: int) -> None:
    q = await db.execute(
        select(SavedVacancy).where(SavedVacancy.candidate_id == candidate_id, SavedVacancy.vacancy_id == vacancy_id)
    )
    row = q.scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()


async def list_favorites(
    db: AsyncSession,
    candidate_id: int,
    *,
    q: str | None = None,
    location: str | None = None,
    company_name: str | None = None,
) -> list[SavedVacancy]:
    stmt = (
        select(SavedVacancy)
        .join(Vacancy, Vacancy.id == SavedVacancy.vacancy_id)
        .options(selectinload(SavedVacancy.vacancy))
        .where(SavedVacancy.candidate_id == candidate_id)
        .order_by(SavedVacancy.created_at.desc())
    )
    if q:
        like = f"%{q.strip()}%"
        from sqlalchemy import or_

        stmt = stmt.where(
            or_(Vacancy.title.ilike(like), Vacancy.company_name.ilike(like), Vacancy.location.ilike(like))
        )
    if location:
        stmt = stmt.where(Vacancy.location.ilike(f"%{location.strip()}%"))
    if company_name:
        stmt = stmt.where(Vacancy.company_name.ilike(f"%{company_name.strip()}%"))
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def run_saved_search(
    db: AsyncSession, candidate_id: int, search_id: int, *, page: int = 1, page_size: int = 20
) -> tuple[list[Vacancy], int]:
    q = await db.execute(
        select(SavedSearch).where(SavedSearch.id == search_id, SavedSearch.candidate_id == candidate_id)
    )
    row = q.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saqlangan qidiruv topilmadi.")
    try:
        filters = json.loads(row.filters_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filter JSON noto'g'ri.") from exc

    def _enum(cls, key: str):
        val = filters.get(key)
        if val is None:
            return None
        return cls(val)

    return await list_active_vacancies(
        db,
        q=filters.get("q"),
        location=filters.get("location"),
        company_name=filters.get("company_name"),
        employment_type=_enum(EmploymentType, "employment_type"),
        work_mode=_enum(WorkMode, "work_mode"),
        experience_level=_enum(ExperienceLevel, "experience_level"),
        industry=filters.get("industry"),
        skill=filters.get("skill"),
        remote_only=filters.get("remote_only"),
        verified_company_only=filters.get("verified_company_only"),
        posted_within_days=filters.get("posted_within_days"),
        salary_from=filters.get("salary_from"),
        salary_to=filters.get("salary_to"),
        salary_currency=filters.get("salary_currency"),
        salary_negotiable=filters.get("salary_negotiable"),
        sort_by=filters.get("sort_by", "date_desc"),
        page=page,
        page_size=page_size,
        candidate_id=candidate_id,
        exclude_applied=bool(filters.get("exclude_applied", False)),
        favorites_only=bool(filters.get("favorites_only", False)),
    )


async def create_saved_search(db: AsyncSession, candidate_id: int, name: str, filters_json: str) -> SavedSearch:
    row = SavedSearch(candidate_id=candidate_id, name=name, filters_json=filters_json)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def list_saved_searches(db: AsyncSession, candidate_id: int) -> list[SavedSearch]:
    q = await db.execute(
        select(SavedSearch).where(SavedSearch.candidate_id == candidate_id).order_by(SavedSearch.created_at.desc())
    )
    return list(q.scalars().all())
