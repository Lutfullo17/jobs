"""
Laziz, Aziz Ali, Vali — uchala nomzod akkaunti (@gmail.com, tekshirilgan).

Loyiha ildizidan Docker (tavsiya):

    docker compose run --rm -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/jobify app python scripts/seed_team_laziz_aziz_vali.py

Parolni o'zgartirish: muhitda SEED_TEAM_PASSWORD (default skript ichida).
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole

# Gmail manzillar (login uchun); haqiqiy pochtaga xat yuborilishi shart emas — is_verified=True.
USERS: list[tuple[str, str]] = [
    ("laziz@gmail.com", "Laziz"),
    ("azizali@gmail.com", "Aziz Ali"),
    ("vali@gmail.com", "Vali"),
]

DEFAULT_PASSWORD = "LazizAzizVali2026!"


async def main() -> None:
    password = os.environ.get("SEED_TEAM_PASSWORD", DEFAULT_PASSWORD)
    async with AsyncSessionLocal() as db:
        for email, _name in USERS:
            r = await db.execute(select(User).where(User.email == email))
            if r.scalar_one_or_none():
                print(f"[skip] {email} allaqachon bor")
                continue
            db.add(
                User(
                    email=email,
                    password_hash=hash_password(password),
                    role=UserRole.candidate,
                    is_active=True,
                    is_verified=True,
                    hr_approved=True,
                )
            )
            print(f"[ok] {email}")
        await db.commit()

    print()
    print("Login (har biri uchun bir xil parol, SEED_TEAM_PASSWORD bo'lmasa default):")
    for email, name in USERS:
        print(f"  {name}: {email}")
    print(f"  parol: {password}")


if __name__ == "__main__":
    asyncio.run(main())
