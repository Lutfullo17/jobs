"""Nomzod: bildirishnomalar va dashboard."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_candidate
from app.models.user import User
from app.models.vacancy import VacancyApplication
from app.schemas.common import MessageResponse
from app.schemas.platform import CandidateDashboardOut, NotificationOut, PipelineStageCount
from app.services.candidate_profile_service import calc_completeness, get_or_create_profile
from app.services.notification_service import count_unread, list_notifications, mark_notification_read

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
    return CandidateDashboardOut(
        applications_total=sum(s.count for s in by_status),
        applications_by_status=by_status,
        unread_notifications=await count_unread(db, candidate.id),
        profile_completeness_percent=calc_completeness(profile),
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
