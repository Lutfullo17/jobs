"""
Nomzod: murojaat tarixini ko'rish va HR `chat_open` qilgandan keyin xabarlar.

Dastlabki matn — `POST /api/vacancies/{id}/apply/`.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_candidate
from app.models.user import User
from app.models.vacancy import ApplicationStatus
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


@router.get("/applications/", response_model=list[ApplicationDetailOut])
async def my_applications(
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
    status: ApplicationStatus | None = Query(None),
    vacancy_id: int | None = Query(None, ge=1),
    q: str | None = Query(None, description="Vacancy title/company/location yoki initial_message bo'yicha qidirish"),
) -> list[ApplicationDetailOut]:
    rows = await list_candidate_applications_filtered(
        db,
        candidate_id=candidate.id,
        status=status,
        vacancy_id=vacancy_id,
        q=q,
    )
    return [_to_detail(a, candidate.email) for a in rows]


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


def _resume_out(row, *, base_url: str = "http://127.0.0.1:8001") -> CandidateResumeOut:
    return CandidateResumeOut(
        id=row.id,
        candidate_id=row.candidate_id,
        original_filename=row.original_filename,
        content_type=row.content_type,
        size_bytes=row.size_bytes,
        created_at=row.created_at,
        updated_at=row.updated_at,
        download_url=f"{base_url}/api/candidate/resume/download/",
    )


@router.get("/resume/", response_model=CandidateResumeOut | None)
async def get_my_resume(
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> CandidateResumeOut | None:
    row = await get_candidate_resume(db, candidate_id=candidate.id)
    return _resume_out(row) if row else None


@router.get("/resume/download/")
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
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> CandidateResumeOut:
    row = await upsert_candidate_resume(db, candidate_id=candidate.id, file=file)
    return _resume_out(row)


@router.put("/resume/", response_model=CandidateResumeOut)
async def update_resume(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> CandidateResumeOut:
    row = await upsert_candidate_resume(db, candidate_id=candidate.id, file=file)
    return _resume_out(row)


@router.delete("/resume/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> None:
    await delete_candidate_resume(db, candidate_id=candidate.id)
    return None
