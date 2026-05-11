"""
Vakansiya + murojaat qoidalari (ustoz uchun qisqa):

1) Nomzod bir vakansiyaga faqat bir marta murojaat yubora oladi (unique constraint).
2) O'sha bitta martalik matn — `VacancyApplication.initial_message`.
3) HR "qabul" desa (`chat_open`) — `application_messages` jadvalida yozishish boshlanadi.
4) HR "rad" desa (`rejected`) — yangi xabar yo'q.

Technik tekshiruvlar: vacancy o'chirilgan bo'lsa/yoki HR boshqasining vakansi bo'lsa → 403/404.
"""

from datetime import UTC, datetime

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.models.vacancy import ApplicationMessage, ApplicationStatus, EmploymentType, Vacancy, VacancyApplication, WorkMode
from app.schemas.hr_vacancy import VacancyCreateBody


# ----- umumiy (ochiq ro'yxat) -----


async def list_active_vacancies(
    db: AsyncSession,
    *,
    q: str | None = None,
    location: str | None = None,
    company_name: str | None = None,
    employment_type: EmploymentType | None = None,
    work_mode: WorkMode | None = None,
    salary_from: int | None = None,
    salary_to: int | None = None,
    salary_currency: str | None = None,
    salary_negotiable: bool | None = None,
) -> list[Vacancy]:
    today = datetime.now(UTC).date()
    stmt = (
        select(Vacancy)
        .where(
            Vacancy.is_deleted.is_(False),
            or_(Vacancy.expires_at.is_(None), Vacancy.expires_at >= today),
        )
        .order_by(Vacancy.created_at.desc())
    )

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Vacancy.title.ilike(like), Vacancy.description.ilike(like)))
    if location:
        stmt = stmt.where(Vacancy.location.ilike(f"%{location.strip()}%"))
    if company_name:
        stmt = stmt.where(Vacancy.company_name.ilike(f"%{company_name.strip()}%"))
    if employment_type is not None:
        stmt = stmt.where(Vacancy.employment_type == employment_type)
    if work_mode is not None:
        stmt = stmt.where(Vacancy.work_mode == work_mode)
    if salary_currency:
        stmt = stmt.where(Vacancy.salary_currency == salary_currency.strip())
    if salary_negotiable is not None:
        stmt = stmt.where(Vacancy.salary_negotiable.is_(salary_negotiable))

    # salary range filter (nullable ustunlar bilan ehtiyotkor)
    salary_clauses = []
    if salary_from is not None:
        salary_clauses.append(or_(Vacancy.salary_to.is_(None), Vacancy.salary_to >= salary_from))
    if salary_to is not None:
        salary_clauses.append(or_(Vacancy.salary_from.is_(None), Vacancy.salary_from <= salary_to))
    if salary_clauses:
        stmt = stmt.where(and_(*salary_clauses))

    res = await db.execute(stmt)
    return list(res.scalars().all())


async def get_active_vacancy(db: AsyncSession, vacancy_id: int) -> Vacancy | None:
    today = datetime.now(UTC).date()
    q = await db.execute(
        select(Vacancy).where(
            Vacancy.id == vacancy_id,
            Vacancy.is_deleted.is_(False),
            or_(Vacancy.expires_at.is_(None), Vacancy.expires_at >= today),
        )
    )
    return q.scalar_one_or_none()


# ----- HR: vakansiya CRUD -----


async def create_vacancy(db: AsyncSession, *, hr_id: int, payload: VacancyCreateBody) -> Vacancy:
    v = Vacancy(
        hr_id=hr_id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        company_name=payload.company_name.strip(),
        location=payload.location.strip(),
        employment_type=payload.employment_type,
        work_mode=payload.work_mode,
        salary_from=payload.salary_from,
        salary_to=payload.salary_to,
        salary_currency=payload.salary_currency.strip(),
        salary_negotiable=payload.salary_negotiable,
        responsibilities=payload.responsibilities.strip(),
        requirements=payload.requirements.strip(),
        benefits=payload.benefits.strip(),
        experience_note=payload.experience_note.strip(),
        education_note=payload.education_note.strip(),
        contact_phone=payload.contact_phone.strip() if payload.contact_phone else None,
        expires_at=payload.expires_at,
        is_deleted=False,
    )
    db.add(v)
    await db.commit()
    await db.refresh(v)
    return v


async def list_hr_vacancies(db: AsyncSession, hr_id: int) -> list[Vacancy]:
    q = await db.execute(
        select(Vacancy)
        .where(Vacancy.hr_id == hr_id, Vacancy.is_deleted.is_(False))
        .order_by(Vacancy.created_at.desc())
    )
    return list(q.scalars().all())


async def get_hr_vacancy(db: AsyncSession, vacancy_id: int, hr_id: int) -> Vacancy:
    q = await db.execute(
        select(Vacancy).where(Vacancy.id == vacancy_id, Vacancy.hr_id == hr_id, Vacancy.is_deleted.is_(False))
    )
    v = q.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vakansiya topilmadi.")
    return v


async def soft_delete_vacancy(db: AsyncSession, vacancy_id: int, hr_id: int) -> None:
    v = await get_hr_vacancy(db, vacancy_id, hr_id)
    v.is_deleted = True
    await db.commit()


# ----- nomzod: murojaat -----


async def apply_to_vacancy(
    db: AsyncSession,
    *,
    vacancy_id: int,
    candidate: User,
    message: str,
) -> VacancyApplication:
    if candidate.role != UserRole.candidate:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faqat nomzod murojaat yubora oladi.")

    v = await get_active_vacancy(db, vacancy_id)
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vakansiya topilmadi yoki olib tashlangan.")

    app_row = VacancyApplication(
        vacancy_id=v.id,
        candidate_id=candidate.id,
        initial_message=message.strip(),
        status=ApplicationStatus.pending,
    )
    db.add(app_row)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu vakansiyaga allaqachon murojaat yuborgansiz (bitta marta).",
        ) from exc
    await db.refresh(app_row)
    return app_row


async def list_candidate_applications(db: AsyncSession, candidate_id: int) -> list[VacancyApplication]:
    q = await db.execute(
        select(VacancyApplication)
        .options(
            selectinload(VacancyApplication.vacancy),
            selectinload(VacancyApplication.candidate),
            selectinload(VacancyApplication.chat_messages),
        )
        .where(VacancyApplication.candidate_id == candidate_id)
        .order_by(VacancyApplication.created_at.desc())
    )
    return list(q.scalars().all())


async def list_candidate_applications_filtered(
    db: AsyncSession,
    *,
    candidate_id: int,
    status: ApplicationStatus | None = None,
    vacancy_id: int | None = None,
    q: str | None = None,
) -> list[VacancyApplication]:
    stmt = (
        select(VacancyApplication)
        .join(Vacancy, Vacancy.id == VacancyApplication.vacancy_id)
        .options(
            selectinload(VacancyApplication.vacancy),
            selectinload(VacancyApplication.candidate),
            selectinload(VacancyApplication.chat_messages),
        )
        .where(VacancyApplication.candidate_id == candidate_id)
        .order_by(VacancyApplication.created_at.desc())
    )
    if status is not None:
        stmt = stmt.where(VacancyApplication.status == status)
    if vacancy_id is not None:
        stmt = stmt.where(VacancyApplication.vacancy_id == vacancy_id)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Vacancy.title.ilike(like),
                Vacancy.company_name.ilike(like),
                Vacancy.location.ilike(like),
                VacancyApplication.initial_message.ilike(like),
            )
        )
    res = await db.execute(stmt)
    return list(res.scalars().all())


# ----- HR: murojaatlar -----


def _applications_for_hr_query(hr_id: int) -> Select:
    return (
        select(VacancyApplication)
        .join(Vacancy, Vacancy.id == VacancyApplication.vacancy_id)
        .options(selectinload(VacancyApplication.vacancy), selectinload(VacancyApplication.candidate))
        .where(Vacancy.hr_id == hr_id)
        .order_by(VacancyApplication.created_at.desc())
    )


async def list_hr_applications(db: AsyncSession, hr_id: int) -> list[VacancyApplication]:
    q = await db.execute(_applications_for_hr_query(hr_id))
    return list(q.scalars().all())


async def list_hr_applications_filtered(
    db: AsyncSession,
    *,
    hr_id: int,
    status: ApplicationStatus | None = None,
    vacancy_id: int | None = None,
    q: str | None = None,
) -> list[VacancyApplication]:
    stmt = _applications_for_hr_query(hr_id)
    if status is not None:
        stmt = stmt.where(VacancyApplication.status == status)
    if vacancy_id is not None:
        stmt = stmt.where(VacancyApplication.vacancy_id == vacancy_id)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Vacancy.title.ilike(like),
                Vacancy.company_name.ilike(like),
                Vacancy.location.ilike(like),
                VacancyApplication.initial_message.ilike(like),
            )
        )
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def get_application_for_hr(db: AsyncSession, application_id: int, hr_id: int) -> VacancyApplication:
    q = await db.execute(
        select(VacancyApplication)
        .join(Vacancy, Vacancy.id == VacancyApplication.vacancy_id)
        .options(
            selectinload(VacancyApplication.vacancy),
            selectinload(VacancyApplication.candidate),
            selectinload(VacancyApplication.chat_messages),
        )
        .where(VacancyApplication.id == application_id, Vacancy.hr_id == hr_id)
    )
    app_row = q.scalar_one_or_none()
    if not app_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Murojaat topilmadi.")
    return app_row


async def get_application_for_candidate(db: AsyncSession, application_id: int, candidate_id: int) -> VacancyApplication:
    q = await db.execute(
        select(VacancyApplication)
        .options(
            selectinload(VacancyApplication.vacancy),
            selectinload(VacancyApplication.candidate),
            selectinload(VacancyApplication.chat_messages),
        )
        .where(VacancyApplication.id == application_id, VacancyApplication.candidate_id == candidate_id)
    )
    app_row = q.scalar_one_or_none()
    if not app_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Murojaat topilmadi.")
    return app_row


async def accept_application(db: AsyncSession, *, application_id: int, hr: User) -> VacancyApplication:
    if hr.role != UserRole.hr:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faqat HR.")
    app_row = await get_application_for_hr(db, application_id, hr.id)
    if app_row.status != ApplicationStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Faqat kutilayotgan murojaatni ochish mumkin.")
    app_row.status = ApplicationStatus.chat_open
    await db.commit()
    await db.refresh(app_row)
    return app_row


async def reject_application(db: AsyncSession, *, application_id: int, hr: User) -> VacancyApplication:
    if hr.role != UserRole.hr:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faqat HR.")
    app_row = await get_application_for_hr(db, application_id, hr.id)
    if app_row.status != ApplicationStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Faqat kutilayotgan murojaatni rad etish mumkin.")
    app_row.status = ApplicationStatus.rejected
    await db.commit()
    await db.refresh(app_row)
    return app_row


async def append_chat_message(db: AsyncSession, *, application_id: int, sender: User, body: str) -> ApplicationMessage:
    """Faqat `chat_open`: HR (shu vakansiya egasi) yoki nomzod."""
    msg_text = body.strip()
    q = await db.execute(
        select(VacancyApplication)
        .options(selectinload(VacancyApplication.vacancy))
        .where(VacancyApplication.id == application_id)
    )
    app_row = q.scalar_one_or_none()
    if not app_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Murojaat topilmadi.")

    if app_row.status != ApplicationStatus.chat_open:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Suhbat hali ochilmagan yoki rad etilgan.",
        )

    v = app_row.vacancy
    allowed = False
    if sender.role == UserRole.candidate and app_row.candidate_id == sender.id:
        allowed = True
    if sender.role == UserRole.hr and v.hr_id == sender.id:
        allowed = True
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu murojaatga yozishga ruxsat yo'q.")

    row = ApplicationMessage(application_id=app_row.id, sender_id=sender.id, body=msg_text)
    db.add(row)
    app_row.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(row)
    return row
