from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.candidate_profile import (
    CandidateCertificate,
    CandidateEducation,
    CandidateExperience,
    CandidateLanguage,
    CandidateProfile,
    CandidateSkill,
    PreferredWorkMode,
)
from app.models.user import User
from app.schemas.candidate_profile import ProfileFullUpdateBody, ProfileUpdateBody


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
    if profile.experiences:
        filled += 1
    if profile.skills:
        filled += 1
    if profile.educations:
        filled += 1
    total = 9
    return min(100, int(filled / total * 100))


async def get_or_create_profile(db: AsyncSession, user: User) -> CandidateProfile:
    q = await db.execute(
        select(CandidateProfile)
        .options(
            selectinload(CandidateProfile.experiences),
            selectinload(CandidateProfile.educations),
            selectinload(CandidateProfile.skills),
            selectinload(CandidateProfile.languages),
            selectinload(CandidateProfile.certificates),
        )
        .where(CandidateProfile.user_id == user.id)
    )
    profile = q.scalar_one_or_none()
    if profile:
        return profile
    profile = CandidateProfile(user_id=user.id, preferred_work_mode=PreferredWorkMode.any)
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def update_profile(db: AsyncSession, user: User, payload: ProfileUpdateBody | ProfileFullUpdateBody) -> CandidateProfile:
    profile = await get_or_create_profile(db, user)
    data = payload.model_dump(exclude_unset=True, exclude={"experiences", "educations", "skills", "languages", "certificates"})
    for k, v in data.items():
        setattr(profile, k, v)

    if isinstance(payload, ProfileFullUpdateBody):
        if payload.experiences is not None:
            profile.experiences.clear()
            for e in payload.experiences:
                profile.experiences.append(CandidateExperience(**e.model_dump()))
        if payload.educations is not None:
            profile.educations.clear()
            for e in payload.educations:
                profile.educations.append(CandidateEducation(**e.model_dump()))
        if payload.skills is not None:
            profile.skills.clear()
            for s in payload.skills:
                profile.skills.append(CandidateSkill(**s.model_dump()))
        if payload.languages is not None:
            profile.languages.clear()
            for lang in payload.languages:
                profile.languages.append(CandidateLanguage(**lang.model_dump()))
        if payload.certificates is not None:
            profile.certificates.clear()
            for c in payload.certificates:
                profile.certificates.append(CandidateCertificate(**c.model_dump()))

    await db.commit()
    await db.refresh(profile)
    return profile


async def get_profile_by_user_id(db: AsyncSession, user_id: int) -> CandidateProfile | None:
    q = await db.execute(
        select(CandidateProfile)
        .options(
            selectinload(CandidateProfile.experiences),
            selectinload(CandidateProfile.educations),
            selectinload(CandidateProfile.skills),
            selectinload(CandidateProfile.languages),
            selectinload(CandidateProfile.certificates),
        )
        .where(CandidateProfile.user_id == user_id, CandidateProfile.profile_visible.is_(True))
    )
    return q.scalar_one_or_none()
