"""
Nomzod: murojaat tarixini ko'rish va HR `chat_open` qilgandan keyin xabarlar.

Dastlabki matn — `POST /api/vacancies/{id}/apply/`.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_candidate
from app.models.user import User
from app.schemas.hr_vacancy import (
    ApplicationDetailOut,
    ChatMessageOut,
    RecruitmentChatBody,
    RecruitmentChatResponse,
)
from app.services.vacancy_application_service import (
    append_chat_message,
    get_application_for_candidate,
    list_candidate_applications,
)

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
) -> list[ApplicationDetailOut]:
    rows = await list_candidate_applications(db, candidate.id)
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
