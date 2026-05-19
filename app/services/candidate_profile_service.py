from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.candidate_profile import CandidateProfile, PreferredWorkMode
from app.models.user import User

_PROFILE_RELATIONS_LOAD = (
    selectinload(CandidateProfile.experiences),
    selectinload(CandidateProfile.educations),
    selectinload(CandidateProfile.skills),
    selectinload(CandidateProfile.languages),
    selectinload(CandidateProfile.certificates),
)


def _rel_nonempty(profile: CandidateProfile, name: str) -> bool:
    """Yuklanmagan bog'lanishda async lazy load qilmasdan False qaytaradi."""
    state = sa_inspect(profile)
    if name in state.unloaded:
        return False
    return bool(getattr(profile, name))


def calc_completeness(profile: CandidateProfile) -> int:
    fields = [
        profile.first_name,
        profile.last_name,
        profile.phone,
        profile.city,
        profile.country,
        profile.about_me,
    ]
    filled = sum(1 for f in fields if f)
    if _rel_nonempty(profile, "experiences"):
        filled += 1
    if _rel_nonempty(profile, "skills"):
        filled += 1
    if _rel_nonempty(profile, "educations"):
        filled += 1
    total = 9
    return min(100, int(filled / total * 100))


async def get_or_create_profile(db: AsyncSession, user: User) -> CandidateProfile:
    q = await db.execute(
        select(CandidateProfile)
        .options(*_PROFILE_RELATIONS_LOAD)
        .where(CandidateProfile.user_id == user.id)
    )
    profile = q.scalar_one_or_none()
    if profile:
        return profile
    profile = CandidateProfile(user_id=user.id, preferred_work_mode=PreferredWorkMode.any)
    db.add(profile)
    await db.commit()
    q2 = await db.execute(
        select(CandidateProfile).options(*_PROFILE_RELATIONS_LOAD).where(CandidateProfile.id == profile.id)
    )
    return q2.scalar_one()


async def get_profile_by_user_id(db: AsyncSession, user_id: int) -> CandidateProfile | None:
    q = await db.execute(
        select(CandidateProfile)
        .options(*_PROFILE_RELATIONS_LOAD)
        .where(CandidateProfile.user_id == user_id, CandidateProfile.profile_visible.is_(True))
    )
    return q.scalar_one_or_none()
