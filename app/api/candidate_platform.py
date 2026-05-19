"""Nomzod: sevimlilar, bildirishnomalar, dashboard, intervyular, saqlangan qidiruv."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_candidate
from app.models.platform import SavedSearch, SavedVacancy
from app.models.user import User
from app.models.vacancy import ApplicationStatus, VacancyApplication
from app.models.vacancy import EmploymentType, ExperienceLevel, WorkMode
from app.schemas.candidate_search import CandidateVacancyListItem
from app.schemas.common import MessageResponse, PaginatedResponse, paginate
from app.schemas.hr_vacancy import VacancyPublicListItem
from app.schemas.platform import (
    CandidateDashboardOut,
    InterviewOut,
    NotificationOut,
    PipelineStageCount,
    SavedSearchCreateBody,
    SavedSearchOut,
    SavedVacancyOut,
)
from app.services.candidate_profile_service import calc_completeness, get_or_create_profile
from app.services.favorites_service import (
    add_favorite,
    create_saved_search,
    list_favorites,
    list_saved_searches,
    remove_favorite,
    run_saved_search,
)
from app.services.vacancy_application_service import get_candidate_vacancy_meta
from app.services.interview_service import confirm_interview, decline_interview
from app.services.notification_service import count_unread, list_notifications, mark_notification_read
from app.services.vacancy_application_service import withdraw_application

router = APIRouter(prefix="/api/candidate", tags=["Nomzod — platforma"])


@router.get("/dashboard/", response_model=CandidateDashboardOut)
async def candidate_dashboard(
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> CandidateDashboardOut:
    profile = await get_or_create_profile(db, candidate)
    status_q = await db.execute(
        select(VacancyApplication.status, func.count())
        .where(VacancyApplication.candidate_id == candidate.id)
        .group_by(VacancyApplication.status)
    )
    by_status = [
        PipelineStageCount(status=str(r[0].value if hasattr(r[0], "value") else r[0]), count=r[1])
        for r in status_q.all()
    ]
    fav_count = int(
        (await db.execute(select(func.count()).select_from(SavedVacancy).where(SavedVacancy.candidate_id == candidate.id))).scalar_one()
    )
    search_count = int(
        (await db.execute(select(func.count()).select_from(SavedSearch).where(SavedSearch.candidate_id == candidate.id))).scalar_one()
    )
    return CandidateDashboardOut(
        applications_total=sum(s.count for s in by_status),
        applications_by_status=by_status,
        favorites_count=fav_count,
        unread_notifications=await count_unread(db, candidate.id),
        profile_completeness_percent=calc_completeness(profile),
        saved_searches_count=search_count,
    )


@router.get("/notifications/", response_model=list[NotificationOut])
async def get_notifications(
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> list[NotificationOut]:
    rows = await list_notifications(db, candidate.id, unread_only=unread_only)
    return [NotificationOut.model_validate(r) for r in rows]


@router.post("/notifications/{notification_id}/read/", response_model=MessageResponse)
async def read_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> MessageResponse:
    await mark_notification_read(db, notification_id, candidate.id)
    return MessageResponse(message="O'qildi.")


@router.post("/favorites/{vacancy_id}/", response_model=SavedVacancyOut, status_code=201)
async def save_vacancy(
    vacancy_id: int,
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> SavedVacancyOut:
    row = await add_favorite(db, candidate.id, vacancy_id)
    return SavedVacancyOut.model_validate(row)


@router.delete("/favorites/{vacancy_id}/", status_code=204)
async def unsave_vacancy(
    vacancy_id: int,
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> None:
    await remove_favorite(db, candidate.id, vacancy_id)


@router.get("/favorites/", response_model=list[SavedVacancyOut])
async def list_favorite_vacancies(
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
    q: str | None = Query(None),
    location: str | None = Query(None),
    company_name: str | None = Query(None),
) -> list[SavedVacancyOut]:
    rows = await list_favorites(db, candidate.id, q=q, location=location, company_name=company_name)
    out = []
    for r in rows:
        item = SavedVacancyOut.model_validate(r)
        if r.vacancy:
            item.vacancy = VacancyPublicListItem.model_validate(r.vacancy)
        out.append(item)
    return out


@router.post("/saved-searches/", response_model=SavedSearchOut, status_code=201)
async def save_search(
    payload: SavedSearchCreateBody,
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> SavedSearchOut:
    row = await create_saved_search(db, candidate.id, payload.name, payload.filters_json)
    return SavedSearchOut.model_validate(row)


@router.get("/saved-searches/", response_model=list[SavedSearchOut])
async def get_saved_searches(
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> list[SavedSearchOut]:
    rows = await list_saved_searches(db, candidate.id)
    return [SavedSearchOut.model_validate(r) for r in rows]


@router.get("/saved-searches/{search_id}/results/", response_model=PaginatedResponse[CandidateVacancyListItem])
async def run_saved_search_endpoint(
    search_id: int,
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[CandidateVacancyListItem]:
    rows, total = await run_saved_search(db, candidate.id, search_id, page=page, page_size=page_size)
    ids = [v.id for v in rows]
    applied_ids, saved_ids, app_map = await get_candidate_vacancy_meta(db, candidate.id, ids)
    items = []
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


@router.post("/applications/{application_id}/withdraw/", response_model=MessageResponse)
async def withdraw(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> MessageResponse:
    await withdraw_application(db, application_id, candidate.id)
    return MessageResponse(message="Murojaat bekor qilindi.")


@router.post("/interviews/{interview_id}/confirm/", response_model=InterviewOut)
async def confirm_interview_endpoint(
    interview_id: int,
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> InterviewOut:
    row = await confirm_interview(db, interview_id, candidate)
    return InterviewOut.model_validate(row)


@router.post("/interviews/{interview_id}/decline/", response_model=InterviewOut)
async def decline_interview_endpoint(
    interview_id: int,
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> InterviewOut:
    row = await decline_interview(db, interview_id, candidate)
    return InterviewOut.model_validate(row)
