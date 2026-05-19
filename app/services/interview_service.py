from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import Interview, InterviewStatus, NotificationType
from app.models.user import User, UserRole
from app.models.vacancy import ApplicationStatus
from app.schemas.platform import InterviewScheduleBody
from app.services.notification_service import create_notification
from app.models.vacancy import VacancyApplication
from app.services.vacancy_application_service import get_application_for_hr


async def schedule_interview(
    db: AsyncSession, *, application_id: int, hr: User, payload: InterviewScheduleBody
) -> Interview:
    app_row = await get_application_for_hr(db, application_id, hr.id)
    row = Interview(
        application_id=app_row.id,
        scheduled_at=payload.scheduled_at,
        format=payload.format,
        location_or_link=payload.location_or_link,
        notes=payload.notes,
        status=InterviewStatus.pending,
    )
    app_row.status = ApplicationStatus.interview_scheduled
    db.add(row)
    await create_notification(
        db,
        user_id=app_row.candidate_id,
        ntype=NotificationType.interview_scheduled,
        title="Intervyu belgilandi",
        body=f"Vakansiya: {app_row.vacancy.title if app_row.vacancy else ''}",
        related_entity_type="interview",
        related_entity_id=None,
    )
    await db.commit()
    await db.refresh(row)
    return row


async def confirm_interview(db: AsyncSession, interview_id: int, candidate: User) -> Interview:
    row = await _get_interview_for_candidate(db, interview_id, candidate.id)
    if row.status != InterviewStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Intervyu allaqachon javob berilgan.")
    row.status = InterviewStatus.confirmed
    await db.commit()
    await db.refresh(row)
    return row


async def decline_interview(db: AsyncSession, interview_id: int, candidate: User) -> Interview:
    row = await _get_interview_for_candidate(db, interview_id, candidate.id)
    if row.status not in (InterviewStatus.pending, InterviewStatus.confirmed):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Intervyuni rad etib bo'lmaydi.")
    row.status = InterviewStatus.declined
    await db.commit()
    await db.refresh(row)
    return row


async def _get_interview_for_candidate(db: AsyncSession, interview_id: int, candidate_id: int) -> Interview:
    q = await db.execute(
        select(Interview)
        .join(VacancyApplication, VacancyApplication.id == Interview.application_id)
        .where(Interview.id == interview_id, VacancyApplication.candidate_id == candidate_id)
    )
    row = q.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intervyu topilmadi.")
    return row
