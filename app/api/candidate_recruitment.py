"""
Nomzod: murojaat tarixini ko'rish va HR `chat_open` qilgandan keyin xabarlar.

Dastlabki matn — `POST /api/vacancies/{id}/apply/`.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_candidate
from app.models.user import User
from datetime import datetime

from app.models.vacancy import ApplicationStatus, EmploymentType, WorkMode
from app.schemas.candidate_search import ApplicationFilterOptionsOut, CandidateApplicationListItem
from app.schemas.common import PaginatedResponse, paginate
from app.schemas.hr_vacancy import (
    ApplicationDetailOut,
    ChatMessageOut,
    RecruitmentChatBody,
    RecruitmentChatResponse,
)
from app.schemas.resume import CandidateResumeOut
from app.services.vacancy_application_service import (
    append_chat_message,
    get_application_for_candidate,
    list_candidate_applications_filtered,
)
from app.services.resume_service import delete_candidate_resume, get_candidate_resume, upsert_candidate_resume

router = APIRouter(prefix="/api/candidate", tags=["Nomzod — vakansiya"])


@router.get("/applications/filters/", response_model=ApplicationFilterOptionsOut)
async def application_filter_options() -> ApplicationFilterOptionsOut:
    return ApplicationFilterOptionsOut(
        statuses=[s.value for s in ApplicationStatus],
        employment_types=[e.value for e in EmploymentType],
        work_modes=[w.value for w in WorkMode],
        sort_options=["date_desc", "date_asc", "status"],
    )


def _to_detail(a, fallback_email: str) -> ApplicationDetailOut:
    msgs = sorted(a.chat_messages, key=lambda m: m.created_at)
    vac = a.vacancy
    cand = a.candidate
    return ApplicationDetailOut(
        id=a.id,
        vacancy_id=a.vacancy_id,
        vacancy_title=vac.title if vac else "",
        candidate_id=a.candidate_id,
        candidate_email=cand.email if cand else fallback_email,
        status=a.status,
        initial_message=a.initial_message,
        created_at=a.created_at,
        chat_messages=[ChatMessageOut.model_validate(m) for m in msgs],
    )


@router.get("/applications/", response_model=PaginatedResponse[CandidateApplicationListItem])
async def my_applications(
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
    status: ApplicationStatus | None = Query(None, description="Bitta holat"),
    statuses: list[ApplicationStatus] | None = Query(None, description="Bir nechta holat, masalan applied,screening"),
    vacancy_id: int | None = Query(None, ge=1),
    q: str | None = Query(None, description="Vakansiya nomi / kompaniya / xabar"),
    company_name: str | None = Query(None),
    location: str | None = Query(None),
    work_mode: WorkMode | None = Query(None),
    employment_type: EmploymentType | None = Query(None),
    created_from: datetime | None = Query(None),
    created_to: datetime | None = Query(None),
    active_only: bool | None = Query(None, description="Rad/withdrawn/hired dan tashqari"),
    sort_by: str = Query("date_desc", pattern="^(date_desc|date_asc|status)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[CandidateApplicationListItem]:
    rows, total = await list_candidate_applications_filtered(
        db,
        candidate_id=candidate.id,
        status=status,
        statuses=statuses,
        vacancy_id=vacancy_id,
        q=q,
        company_name=company_name,
        location=location,
        work_mode=work_mode,
        employment_type=employment_type,
        created_from=created_from,
        created_to=created_to,
        active_only=active_only,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    items = []
    for a in rows:
        vac = a.vacancy
        items.append(
            CandidateApplicationListItem(
                id=a.id,
                vacancy_id=a.vacancy_id,
                vacancy_title=vac.title if vac else "",
                company_name=vac.company_name if vac else "",
                location=vac.location if vac else "",
                status=a.status,
                initial_message=a.initial_message,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
        )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=paginate(total, page, page_size),
    )


@router.get("/applications/{application_id}/", response_model=ApplicationDetailOut)
async def application_detail(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> ApplicationDetailOut:
    a = await get_application_for_candidate(db, application_id, candidate.id)
    return _to_detail(a, candidate.email)


@router.post("/applications/{application_id}/messages/", response_model=RecruitmentChatResponse)
async def candidate_send_message(
    application_id: int,
    payload: RecruitmentChatBody,
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> RecruitmentChatResponse:
    await append_chat_message(db, application_id=application_id, sender=candidate, body=payload.message)
    return RecruitmentChatResponse(message="Xabar yuborildi.")


# ---- Nomzod: rezume (CV) CRUD ----


def _resume_out(row, request: Request) -> CandidateResumeOut:
    download_url = str(request.url_for("candidate_download_resume"))
    return CandidateResumeOut(
        id=row.id,
        candidate_id=row.candidate_id,
        original_filename=row.original_filename,
        content_type=row.content_type,
        size_bytes=row.size_bytes,
        created_at=row.created_at,
        updated_at=row.updated_at,
        download_url=download_url,
    )


@router.get("/resume/", response_model=CandidateResumeOut | None)
async def get_my_resume(
    request: Request,
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> CandidateResumeOut | None:
    row = await get_candidate_resume(db, candidate_id=candidate.id)
    return _resume_out(row, request) if row else None


@router.get("/resume/download/", name="candidate_download_resume")
async def download_my_resume(
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
):
    row = await get_candidate_resume(db, candidate_id=candidate.id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rezume topilmadi.")
    path = Path(row.file_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rezume fayli topilmadi.")
    return FileResponse(
        path=str(path),
        media_type=row.content_type,
        filename=row.original_filename,
    )


@router.post("/resume/", response_model=CandidateResumeOut, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    request: Request,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> CandidateResumeOut:
    row = await upsert_candidate_resume(db, candidate_id=candidate.id, file=file)
    return _resume_out(row, request)


@router.put("/resume/", response_model=CandidateResumeOut)
async def update_resume(
    request: Request,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> CandidateResumeOut:
    row = await upsert_candidate_resume(db, candidate_id=candidate.id, file=file)
    return _resume_out(row, request)


@router.delete("/resume/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> None:
    await delete_candidate_resume(db, candidate_id=candidate.id)
    return None
