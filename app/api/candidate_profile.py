"""Nomzod profili (ko'rish)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_candidate
from app.models.user import User
from app.schemas.candidate_profile import CandidateProfileOut
from app.services.candidate_profile_service import calc_completeness, get_or_create_profile

router = APIRouter(prefix="/api/candidate/profile", tags=["Nomzod — profil"])


def _profile_out(profile) -> CandidateProfileOut:
    data = CandidateProfileOut.model_validate(profile)
    data.completeness_percent = calc_completeness(profile)
    return data


@router.get("/", response_model=CandidateProfileOut)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    candidate: User = Depends(require_candidate),
) -> CandidateProfileOut:
    profile = await get_or_create_profile(db, candidate)
    return _profile_out(profile)
