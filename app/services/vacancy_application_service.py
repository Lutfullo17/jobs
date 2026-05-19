"""
Vakansiya + murojaat qoidalari (ustoz uchun qisqa):

1) Nomzod bir vakansiyaga faqat bir marta murojaat yubora oladi (unique constraint).
2) O'sha bitta martalik matn — `VacancyApplication.initial_message`.
3) HR "qabul" desa (`chat_open`) — `application_messages` jadvalida yozishish boshlanadi.
4) HR "rad" desa (`rejected`) — yangi xabar yo'q.

Technik tekshiruvlar: vacancy o'chirilgan bo'lsa/yoki HR boshqasining vakansi bo'lsa → 403/404.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.models.platform import NotificationType
from app.models.vacancy import (
    ApplicationMessage,
    ApplicationStatus,
    CHAT_ACTIVE_STATUSES,
    EmploymentType,
    ExperienceLevel,
    Vacancy,
    VacancyApplication,
    VacancyStatus,
    WorkMode,
)
from app.schemas.hr_vacancy import VacancyCreateBody, VacancyUpdateBody
from app.services.notification_service import create_notification


# ----- umumiy (ochiq ro'yxat) -----


async def list_active_vacancies(
    db: AsyncSession,
    *,
    q: str | None = None,
    location: str | None = None,
    company_name: str | None = None,
    employment_type: EmploymentType | None = None,
    work_mode: WorkMode | None = None,
    experience_level: ExperienceLevel | None = None,
    industry: str | None = None,
    skill: str | None = None,
    remote_only: bool | None = None,
    verified_company_only: bool | None = None,
    posted_within_days: int | None = None,
    salary_from: int | None = None,
    salary_to: int | None = None,
    salary_currency: str | None = None,
    salary_negotiable: bool | None = None,
    sort_by: str = "date_desc",
    page: int = 1,
    page_size: int = 20,
    candidate_id: int | None = None,
    exclude_applied: bool = False,
    favorites_only: bool = False,
) -> tuple[list[Vacancy], int]:
    today = datetime.now(UTC).date()
    stmt = select(Vacancy).where(
        Vacancy.is_deleted.is_(False),
        Vacancy.status == VacancyStatus.published,
        or_(Vacancy.expires_at.is_(None), Vacancy.expires_at >= today),
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
    if experience_level is not None:
        stmt = stmt.where(Vacancy.experience_level == experience_level)
    if industry:
        stmt = stmt.where(Vacancy.industry.ilike(f"%{industry.strip()}%"))
    if skill:
        stmt = stmt.where(Vacancy.skills_required.ilike(f"%{skill.strip()}%"))
    if remote_only:
        stmt = stmt.where(or_(Vacancy.work_mode == WorkMode.remote, Vacancy.is_remote_worldwide.is_(True)))
    if posted_within_days is not None and posted_within_days > 0:
        since = datetime.now(UTC) - timedelta(days=posted_within_days)
        stmt = stmt.where(Vacancy.published_at >= since)
    if verified_company_only:
        from app.models.company import Company

        stmt = stmt.join(Company, Company.id == Vacancy.company_id, isouter=True).where(Company.verified.is_(True))

    if favorites_only and candidate_id:
        from app.models.platform import SavedVacancy

        stmt = stmt.join(SavedVacancy, SavedVacancy.vacancy_id == Vacancy.id).where(
            SavedVacancy.candidate_id == candidate_id
        )
    if exclude_applied and candidate_id:
        applied_ids = select(VacancyApplication.vacancy_id).where(
            VacancyApplication.candidate_id == candidate_id
        )
        stmt = stmt.where(Vacancy.id.not_in(applied_ids))

    if sort_by == "salary_desc":
        stmt = stmt.order_by(Vacancy.salary_to.desc().nullslast(), Vacancy.created_at.desc())
    elif sort_by == "relevance" and q:
        stmt = stmt.order_by(Vacancy.created_at.desc())
    else:
        stmt = stmt.order_by(Vacancy.published_at.desc().nullslast(), Vacancy.created_at.desc())

    subq = stmt.order_by(None).subquery()
    total = int((await db.execute(select(func.count()).select_from(subq))).scalar_one())
    offset = max(0, (page - 1) * page_size)
    res = await db.execute(stmt.offset(offset).limit(page_size))
    return list(res.scalars().all()), total


async def get_active_vacancy(db: AsyncSession, vacancy_id: int) -> Vacancy | None:
    today = datetime.now(UTC).date()
    q = await db.execute(
        select(Vacancy).where(
            Vacancy.id == vacancy_id,
            Vacancy.is_deleted.is_(False),
            Vacancy.status == VacancyStatus.published,
            or_(Vacancy.expires_at.is_(None), Vacancy.expires_at >= today),
        )
    )
    return q.scalar_one_or_none()


# ----- HR: vakansiya CRUD -----


async def create_vacancy(db: AsyncSession, *, hr_id: int, payload: VacancyCreateBody) -> Vacancy:
    v = Vacancy(
        hr_id=hr_id,
        company_id=payload.company_id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        company_name=payload.company_name.strip(),
        location=payload.location.strip(),
        employment_type=payload.employment_type,
        work_mode=payload.work_mode,
        status=VacancyStatus.draft,
        experience_level=payload.experience_level,
        industry=payload.industry.strip(),
        skills_required=payload.skills_required.strip(),
        headcount=payload.headcount,
        screening_questions=payload.screening_questions.strip(),
        is_remote_worldwide=payload.is_remote_worldwide,
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


async def update_vacancy(db: AsyncSession, vacancy_id: int, hr_id: int, payload: VacancyUpdateBody) -> Vacancy:
    v = await get_hr_vacancy(db, vacancy_id, hr_id)
    if v.status not in (VacancyStatus.draft, VacancyStatus.published, VacancyStatus.on_moderation):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bu holatda tahrirlab bo'lmaydi.")
    for k, val in payload.model_dump(exclude_unset=True).items():
        if val is not None and isinstance(val, str):
            setattr(v, k, val.strip() if k not in ("contact_phone",) else val)
        else:
            setattr(v, k, val)
    await db.commit()
    await db.refresh(v)
    return v


async def publish_vacancy(db: AsyncSession, vacancy_id: int, hr_id: int) -> Vacancy:
    v = await get_hr_vacancy(db, vacancy_id, hr_id)
    if v.status not in (VacancyStatus.draft, VacancyStatus.on_moderation):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Faqat draft/moderatsiyadan publish qilinadi.")
    v.status = VacancyStatus.published
    v.published_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(v)
    return v


async def archive_vacancy(db: AsyncSession, vacancy_id: int, hr_id: int) -> Vacancy:
    v = await get_hr_vacancy(db, vacancy_id, hr_id)
    v.status = VacancyStatus.archived
    await db.commit()
    await db.refresh(v)
    return v


async def close_vacancy(db: AsyncSession, vacancy_id: int, hr_id: int) -> Vacancy:
    v = await get_hr_vacancy(db, vacancy_id, hr_id)
    v.status = VacancyStatus.closed
    await db.commit()
    await db.refresh(v)
    return v


async def duplicate_vacancy(db: AsyncSession, vacancy_id: int, hr_id: int) -> Vacancy:
    src = await get_hr_vacancy(db, vacancy_id, hr_id)
    copy = Vacancy(
        hr_id=src.hr_id,
        company_id=src.company_id,
        title=f"{src.title} (nusxa)",
        description=src.description,
        company_name=src.company_name,
        location=src.location,
        employment_type=src.employment_type,
        work_mode=src.work_mode,
        status=VacancyStatus.draft,
        experience_level=src.experience_level,
        industry=src.industry,
        skills_required=src.skills_required,
        headcount=src.headcount,
        screening_questions=src.screening_questions,
        is_remote_worldwide=src.is_remote_worldwide,
        salary_from=src.salary_from,
        salary_to=src.salary_to,
        salary_currency=src.salary_currency,
        salary_negotiable=src.salary_negotiable,
        responsibilities=src.responsibilities,
        requirements=src.requirements,
        benefits=src.benefits,
        experience_note=src.experience_note,
        education_note=src.education_note,
        contact_phone=src.contact_phone,
        expires_at=src.expires_at,
        is_deleted=False,
    )
    db.add(copy)
    await db.commit()
    await db.refresh(copy)
    return copy


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
        status=ApplicationStatus.applied,
    )
    db.add(app_row)
    try:
        await db.flush()
        await create_notification(
            db,
            user_id=v.hr_id,
            ntype=NotificationType.application_submitted,
            title="Yangi murojaat",
            body=f"{candidate.email} — {v.title}",
            related_entity_type="application",
            related_entity_id=app_row.id,
        )
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu vakansiyaga allaqachon murojaat yuborgansiz (bitta marta).",
        ) from exc
    await db.refresh(app_row)
    return app_row


_TERMINAL_APPLICATION_STATUSES = frozenset(
    {ApplicationStatus.rejected, ApplicationStatus.withdrawn, ApplicationStatus.hired}
)


async def get_candidate_vacancy_meta(
    db: AsyncSession, candidate_id: int, vacancy_ids: list[int]
) -> tuple[set[int], set[int], dict[int, VacancyApplication]]:
    """applied_ids, saved_ids, application_by_vacancy_id"""
    if not vacancy_ids:
        return set(), set(), {}
    app_q = await db.execute(
        select(VacancyApplication).where(
            VacancyApplication.candidate_id == candidate_id,
            VacancyApplication.vacancy_id.in_(vacancy_ids),
        )
    )
    apps = list(app_q.scalars().all())
    applied_ids = {a.vacancy_id for a in apps}
    app_map = {a.vacancy_id: a for a in apps}

    from app.models.platform import SavedVacancy

    fav_q = await db.execute(
        select(SavedVacancy.vacancy_id).where(
            SavedVacancy.candidate_id == candidate_id,
            SavedVacancy.vacancy_id.in_(vacancy_ids),
        )
    )
    saved_ids = set(fav_q.scalars().all())
    return applied_ids, saved_ids, app_map


async def list_candidate_applications_filtered(
    db: AsyncSession,
    *,
    candidate_id: int,
    status: ApplicationStatus | None = None,
    statuses: list[ApplicationStatus] | None = None,
    vacancy_id: int | None = None,
    q: str | None = None,
    company_name: str | None = None,
    location: str | None = None,
    work_mode: WorkMode | None = None,
    employment_type: EmploymentType | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    active_only: bool | None = None,
    sort_by: str = "date_desc",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[VacancyApplication], int]:
    stmt = (
        select(VacancyApplication)
        .join(Vacancy, Vacancy.id == VacancyApplication.vacancy_id)
        .options(
            selectinload(VacancyApplication.vacancy),
            selectinload(VacancyApplication.candidate),
            selectinload(VacancyApplication.chat_messages),
        )
        .where(VacancyApplication.candidate_id == candidate_id)
    )
    if status is not None:
        stmt = stmt.where(VacancyApplication.status == status)
    if statuses:
        stmt = stmt.where(VacancyApplication.status.in_(statuses))
    if vacancy_id is not None:
        stmt = stmt.where(VacancyApplication.vacancy_id == vacancy_id)
    if company_name:
        stmt = stmt.where(Vacancy.company_name.ilike(f"%{company_name.strip()}%"))
    if location:
        stmt = stmt.where(Vacancy.location.ilike(f"%{location.strip()}%"))
    if work_mode is not None:
        stmt = stmt.where(Vacancy.work_mode == work_mode)
    if employment_type is not None:
        stmt = stmt.where(Vacancy.employment_type == employment_type)
    if created_from is not None:
        stmt = stmt.where(VacancyApplication.created_at >= created_from)
    if created_to is not None:
        stmt = stmt.where(VacancyApplication.created_at <= created_to)
    if active_only:
        stmt = stmt.where(VacancyApplication.status.not_in(_TERMINAL_APPLICATION_STATUSES))
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

    if sort_by == "date_asc":
        stmt = stmt.order_by(VacancyApplication.created_at.asc())
    elif sort_by == "status":
        stmt = stmt.order_by(VacancyApplication.status.asc(), VacancyApplication.created_at.desc())
    else:
        stmt = stmt.order_by(VacancyApplication.created_at.desc())

    subq = stmt.order_by(None).subquery()
    total = int((await db.execute(select(func.count()).select_from(subq))).scalar_one())
    offset = max(0, (page - 1) * page_size)
    res = await db.execute(stmt.offset(offset).limit(page_size))
    return list(res.scalars().all()), total


# ----- HR: murojaatlar -----


def _applications_for_hr_query(hr_id: int) -> Select:
    return (
        select(VacancyApplication)
        .join(Vacancy, Vacancy.id == VacancyApplication.vacancy_id)
        .options(selectinload(VacancyApplication.vacancy), selectinload(VacancyApplication.candidate))
        .where(Vacancy.hr_id == hr_id)
        .order_by(VacancyApplication.created_at.desc())
    )


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
    return await update_application_status(
        db, application_id=application_id, hr=hr, new_status=ApplicationStatus.screening
    )


async def reject_application(
    db: AsyncSession, *, application_id: int, hr: User, rejection_reason: str | None = None
) -> VacancyApplication:
    return await update_application_status(
        db,
        application_id=application_id,
        hr=hr,
        new_status=ApplicationStatus.rejected,
        rejection_reason=rejection_reason,
    )


async def update_application_status(
    db: AsyncSession,
    *,
    application_id: int,
    hr: User,
    new_status: ApplicationStatus,
    hr_note: str | None = None,
    internal_comment: str | None = None,
    rating: int | None = None,
    rejection_reason: str | None = None,
) -> VacancyApplication:
    if hr.role != UserRole.hr:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faqat HR.")
    app_row = await get_application_for_hr(db, application_id, hr.id)
    if app_row.status in (ApplicationStatus.rejected, ApplicationStatus.withdrawn, ApplicationStatus.hired):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Yakuniy holat — o'zgartirib bo'lmaydi.")
    app_row.status = new_status
    if hr_note is not None:
        app_row.hr_note = hr_note
    if internal_comment is not None:
        app_row.internal_comment = internal_comment
    if rating is not None:
        app_row.rating = rating
    if rejection_reason is not None:
        app_row.rejection_reason = rejection_reason
    await create_notification(
        db,
        user_id=app_row.candidate_id,
        ntype=NotificationType.application_status_changed,
        title="Murojaat holati o'zgardi",
        body=f"Yangi holat: {new_status.value}",
        related_entity_type="application",
        related_entity_id=app_row.id,
    )
    await db.commit()
    await db.refresh(app_row)
    return app_row


async def withdraw_application(db: AsyncSession, application_id: int, candidate_id: int) -> VacancyApplication:
    app_row = await get_application_for_candidate(db, application_id, candidate_id)
    if app_row.status in (ApplicationStatus.hired, ApplicationStatus.rejected, ApplicationStatus.withdrawn):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Murojaatni bekor qilib bo'lmaydi.")
    app_row.status = ApplicationStatus.withdrawn
    await db.commit()
    await db.refresh(app_row)
    return app_row


async def count_applications_by_status(db: AsyncSession, hr_id: int) -> dict[str, int]:
    q = await db.execute(
        select(VacancyApplication.status, func.count())
        .join(Vacancy, Vacancy.id == VacancyApplication.vacancy_id)
        .where(Vacancy.hr_id == hr_id)
        .group_by(VacancyApplication.status)
    )
    return {str(row[0].value if hasattr(row[0], "value") else row[0]): row[1] for row in q.all()}


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

    if app_row.status not in CHAT_ACTIVE_STATUSES:
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
