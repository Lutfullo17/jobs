"""
HR uchun API.

- `/status` — barcha HR (tasdiqlanmagan ham) ko'ra oladi.
- Qolganlari — faqat admin HR ni tasdiqlagach (`require_approved_hr`).
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_approved_hr, require_hr_user
from app.models.user import User
from app.models.vacancy import ApplicationStatus
from app.schemas.hr_vacancy import (
    ApplicationDetailOut,
    ApplicationHrListOut,
    ChatMessageOut,
    HrStatusResponse,
    RecruitmentActionResponse,
    RecruitmentChatBody,
    RecruitmentChatResponse,
    VacancyActionResponse,
    VacancyCreateBody,
    VacancyDeletedResponse,
    VacancyHrItem,
    VacancyUpdateBody,
)
from app.schemas.platform import ApplicationStatusUpdateBody, InterviewOut, InterviewScheduleBody, PipelineStageCount
from app.services.interview_service import schedule_interview
from app.services.vacancy_application_service import (
    accept_application,
    append_chat_message,
    archive_vacancy,
    close_vacancy,
    count_applications_by_status,
    create_vacancy,
    duplicate_vacancy,
    get_application_for_hr,
    list_hr_applications_filtered,
    list_hr_vacancies,
    get_hr_vacancy,
    publish_vacancy,
    reject_application,
    soft_delete_vacancy,
    update_application_status,
    update_vacancy,
)
from app.services.resume_service import get_candidate_resume

router = APIRouter(prefix="/api/hr", tags=["HR"])


@router.get("/status/", response_model=HrStatusResponse)
async def hr_status(current: User = Depends(require_hr_user)) -> HrStatusResponse:
    return HrStatusResponse(
        hr_approved=current.hr_approved,
        can_post_vacancies=current.hr_approved,
    )


# ----- vakansiyalar -----


@router.post("/vacancies/", response_model=VacancyHrItem, status_code=201)
async def post_vacancy(
    payload: VacancyCreateBody,
    db: AsyncSession = Depends(get_db),
    hr: User = Depends(require_approved_hr),
) -> VacancyHrItem:
    v = await create_vacancy(db, hr_id=hr.id, payload=payload)
    return VacancyHrItem.model_validate(v)


@router.get("/vacancies/", response_model=list[VacancyHrItem])
async def get_my_vacancies(
    db: AsyncSession = Depends(get_db),
    hr: User = Depends(require_approved_hr),
) -> list[VacancyHrItem]:
    rows = await list_hr_vacancies(db, hr.id)
    return [VacancyHrItem.model_validate(x) for x in rows]


@router.get("/vacancies/{vacancy_id}/", response_model=VacancyHrItem)
async def get_one_vacancy(
    vacancy_id: int,
    db: AsyncSession = Depends(get_db),
    hr: User = Depends(require_approved_hr),
) -> VacancyHrItem:
    v = await get_hr_vacancy(db, vacancy_id, hr.id)
    return VacancyHrItem.model_validate(v)


@router.put("/vacancies/{vacancy_id}/", response_model=VacancyHrItem)
async def update_vacancy_endpoint(
    vacancy_id: int,
    payload: VacancyUpdateBody,
    db: AsyncSession = Depends(get_db),
    hr: User = Depends(require_approved_hr),
) -> VacancyHrItem:
    v = await update_vacancy(db, vacancy_id, hr.id, payload)
    return VacancyHrItem.model_validate(v)


@router.post("/vacancies/{vacancy_id}/publish/", response_model=VacancyActionResponse)
async def publish_vacancy_endpoint(
    vacancy_id: int, db: AsyncSession = Depends(get_db), hr: User = Depends(require_approved_hr)
) -> VacancyActionResponse:
    v = await publish_vacancy(db, vacancy_id, hr.id)
    return VacancyActionResponse(id=v.id, status=v.status, message="Vakansiya e'lon qilindi.")


@router.post("/vacancies/{vacancy_id}/archive/", response_model=VacancyActionResponse)
async def archive_vacancy_endpoint(
    vacancy_id: int, db: AsyncSession = Depends(get_db), hr: User = Depends(require_approved_hr)
) -> VacancyActionResponse:
    v = await archive_vacancy(db, vacancy_id, hr.id)
    return VacancyActionResponse(id=v.id, status=v.status, message="Arxivlandi.")


@router.post("/vacancies/{vacancy_id}/close/", response_model=VacancyActionResponse)
async def close_vacancy_endpoint(
    vacancy_id: int, db: AsyncSession = Depends(get_db), hr: User = Depends(require_approved_hr)
) -> VacancyActionResponse:
    v = await close_vacancy(db, vacancy_id, hr.id)
    return VacancyActionResponse(id=v.id, status=v.status, message="Yopildi.")


@router.post("/vacancies/{vacancy_id}/duplicate/", response_model=VacancyHrItem, status_code=201)
async def duplicate_vacancy_endpoint(
    vacancy_id: int, db: AsyncSession = Depends(get_db), hr: User = Depends(require_approved_hr)
) -> VacancyHrItem:
    v = await duplicate_vacancy(db, vacancy_id, hr.id)
    return VacancyHrItem.model_validate(v)


@router.delete("/vacancies/{vacancy_id}/", response_model=VacancyDeletedResponse)
async def delete_vacancy_endpoint(
    vacancy_id: int,
    db: AsyncSession = Depends(get_db),
    hr: User = Depends(require_approved_hr),
) -> VacancyDeletedResponse:
    await soft_delete_vacancy(db, vacancy_id, hr.id)
    return VacancyDeletedResponse(message="Vakansiya o'chirildi (yashirin).")


# ----- murojaatlar (nomzodlar yozishmasi) -----


def _detail_out(app_row, *, resume_download_url: str | None = None) -> ApplicationDetailOut:
    msgs = sorted(app_row.chat_messages, key=lambda m: m.created_at)
    vac = app_row.vacancy
    cand = app_row.candidate
    return ApplicationDetailOut(
        id=app_row.id,
        vacancy_id=app_row.vacancy_id,
        vacancy_title=vac.title if vac else "",
        candidate_id=app_row.candidate_id,
        candidate_email=cand.email,
        status=app_row.status,
        initial_message=app_row.initial_message,
        hr_note=app_row.hr_note,
        internal_comment=app_row.internal_comment,
        rating=app_row.rating,
        rejection_reason=app_row.rejection_reason,
        created_at=app_row.created_at,
        resume_download_url=resume_download_url,
        chat_messages=[ChatMessageOut.model_validate(m) for m in msgs],
    )


@router.get("/applications/", response_model=list[ApplicationHrListOut])
async def list_applications_for_my_vacancies(
    request: Request,
    db: AsyncSession = Depends(get_db),
    hr: User = Depends(require_approved_hr),
    status: ApplicationStatus | None = Query(None),
    vacancy_id: int | None = Query(None, ge=1),
    q: str | None = Query(None, description="Vacancy title/company/location yoki initial_message bo'yicha qidirish"),
) -> list[ApplicationHrListOut]:
    rows = await list_hr_applications_filtered(db, hr_id=hr.id, status=status, vacancy_id=vacancy_id, q=q)
    out: list[ApplicationHrListOut] = []
    for a in rows:
        resume = await get_candidate_resume(db, candidate_id=a.candidate_id)
        resume_url = None
        if resume:
            resume_url = str(request.url_for("hr_download_candidate_resume", application_id=a.id))
        out.append(
            ApplicationHrListOut(
                id=a.id,
                vacancy_id=a.vacancy_id,
                vacancy_title=a.vacancy.title if a.vacancy else "",
                candidate_id=a.candidate_id,
                candidate_email=a.candidate.email,
                status=a.status,
                initial_message=a.initial_message,
                hr_note=a.hr_note,
                rating=a.rating,
                rejection_reason=a.rejection_reason,
                created_at=a.created_at,
                resume_download_url=resume_url,
            )
        )
    return out


@router.get("/applications/{application_id}/", response_model=ApplicationDetailOut)
async def hr_application_detail(
    application_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    hr: User = Depends(require_approved_hr),
) -> ApplicationDetailOut:
    a = await get_application_for_hr(db, application_id, hr.id)
    resume = await get_candidate_resume(db, candidate_id=a.candidate_id)
    resume_url = str(request.url_for("hr_download_candidate_resume", application_id=a.id)) if resume else None
    return _detail_out(a, resume_download_url=resume_url)


@router.get("/applications/{application_id}/resume/", name="hr_download_candidate_resume")
async def download_candidate_resume_for_hr(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    hr: User = Depends(require_approved_hr),
):
    app_row = await get_application_for_hr(db, application_id, hr.id)
    resume = await get_candidate_resume(db, candidate_id=app_row.candidate_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nomzod rezumesi topilmadi.")
    file_path = Path(resume.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rezume fayli topilmadi.")
    return FileResponse(path=str(file_path), media_type=resume.content_type, filename=resume.original_filename)


@router.post("/applications/{application_id}/accept/", response_model=RecruitmentActionResponse)
async def accept_candidate_chat(
    application_id: int,
    db: AsyncSession = Depends(get_db),
    hr: User = Depends(require_approved_hr),
) -> RecruitmentActionResponse:
    a = await accept_application(db, application_id=application_id, hr=hr)
    return RecruitmentActionResponse(
        application_id=a.id,
        status=a.status,
        message="Nomzod bilan qo'shimcha yozishish ochildi.",
    )


@router.post("/applications/{application_id}/reject/", response_model=RecruitmentActionResponse)
async def reject_candidate(
    application_id: int,
    rejection_reason: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    hr: User = Depends(require_approved_hr),
) -> RecruitmentActionResponse:
    a = await reject_application(db, application_id=application_id, hr=hr, rejection_reason=rejection_reason)
    return RecruitmentActionResponse(application_id=a.id, status=a.status, message="Murojaat rad etildi.")


@router.patch("/applications/{application_id}/status/", response_model=RecruitmentActionResponse)
async def patch_application_status(
    application_id: int,
    payload: ApplicationStatusUpdateBody,
    db: AsyncSession = Depends(get_db),
    hr: User = Depends(require_approved_hr),
) -> RecruitmentActionResponse:
    a = await update_application_status(
        db,
        application_id=application_id,
        hr=hr,
        new_status=payload.status,
        hr_note=payload.hr_note,
        internal_comment=payload.internal_comment,
        rating=payload.rating,
        rejection_reason=payload.rejection_reason,
    )
    return RecruitmentActionResponse(application_id=a.id, status=a.status, message="Holat yangilandi.")


@router.get("/applications/pipeline/", response_model=list[PipelineStageCount])
async def pipeline_counts(
    db: AsyncSession = Depends(get_db),
    hr: User = Depends(require_approved_hr),
) -> list[PipelineStageCount]:
    counts = await count_applications_by_status(db, hr.id)
    return [PipelineStageCount(status=k, count=v) for k, v in counts.items()]


@router.post("/applications/{application_id}/schedule-interview/", response_model=InterviewOut, status_code=201)
async def schedule_interview_endpoint(
    application_id: int,
    payload: InterviewScheduleBody,
    db: AsyncSession = Depends(get_db),
    hr: User = Depends(require_approved_hr),
) -> InterviewOut:
    row = await schedule_interview(db, application_id=application_id, hr=hr, payload=payload)
    return InterviewOut.model_validate(row)


@router.post("/applications/{application_id}/messages/", response_model=RecruitmentChatResponse)
async def hr_send_chat_message(
    application_id: int,
    payload: RecruitmentChatBody,
    db: AsyncSession = Depends(get_db),
    hr: User = Depends(require_approved_hr),
) -> RecruitmentChatResponse:
    await append_chat_message(db, application_id=application_id, sender=hr, body=payload.message)
    return RecruitmentChatResponse(message="Xabar yuborildi.")
