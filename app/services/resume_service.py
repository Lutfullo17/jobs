from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate_resume import CandidateResume


ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

MAX_RESUME_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _uploads_root() -> Path:
    return Path("uploads") / "resumes"


def _safe_filename(name: str) -> str:
    # simple, OS-safe filename
    base = os.path.basename(name).strip()
    if not base:
        return "resume"
    return "".join(c for c in base if c.isalnum() or c in ("-", "_", ".", " ")).strip() or "resume"


async def get_candidate_resume(db: AsyncSession, *, candidate_id: int) -> CandidateResume | None:
    res = await db.execute(select(CandidateResume).where(CandidateResume.candidate_id == candidate_id))
    return res.scalar_one_or_none()


async def upsert_candidate_resume(
    db: AsyncSession,
    *,
    candidate_id: int,
    file: UploadFile,
) -> CandidateResume:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Faqat PDF/DOC/DOCX rezume yuklash mumkin.",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Fayl bo'sh.")
    if len(data) > MAX_RESUME_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Rezume 10MB dan oshmasin.")

    existing = await get_candidate_resume(db, candidate_id=candidate_id)

    uploads_dir = _uploads_root() / str(candidate_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _safe_filename(file.filename or "resume")
    stored_name = f"{uuid4().hex}_{safe_name}"
    rel_path = uploads_dir / stored_name
    abs_path = rel_path.resolve()

    abs_path.write_bytes(data)

    if existing:
        # delete old file if exists
        try:
            Path(existing.file_path).unlink(missing_ok=True)
        except Exception:
            pass
        existing.file_path = str(abs_path)
        existing.original_filename = safe_name
        existing.content_type = file.content_type or "application/octet-stream"
        existing.size_bytes = len(data)
        await db.commit()
        await db.refresh(existing)
        return existing

    row = CandidateResume(
        candidate_id=candidate_id,
        file_path=str(abs_path),
        original_filename=safe_name,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(data),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def delete_candidate_resume(db: AsyncSession, *, candidate_id: int) -> None:
    existing = await get_candidate_resume(db, candidate_id=candidate_id)
    if not existing:
        return
    try:
        Path(existing.file_path).unlink(missing_ok=True)
    except Exception:
        pass
    await db.delete(existing)
    await db.commit()

