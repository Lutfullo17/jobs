"""
Birinchi adminni yaratish (1-variant: faqat CLI / server).

Nega register emas?
- Admin rolini ochiq API orqali berish xavfli — kimdir o'zi admin bo'lib qolishi mumkin.
- Shuning uchun admin faqat ishonchli odam `python` bilan yaratadi.

Ishlatish (loyiha ildizidan, .env da DATABASE_URL to'g'ri bo'lishi kerak):

    python scripts/create_admin.py --email admin@example.com --password "KuchliParol123"

Keyin shu email/parol bilan /api/auth/login/ qilib token oling.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Skriptni har qayerdan ishlatsa ham `app` import topsin
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole


async def main() -> None:
    p = argparse.ArgumentParser(description="PostgreSQL ga bitta admin yozadi.")
    p.add_argument("--email", required=True)
    p.add_argument("--password", required=True)
    args = p.parse_args()

    async with AsyncSessionLocal() as db:
        exists = await db.execute(select(User).where(User.email == args.email))
        if exists.scalar_one_or_none():
            print("Bu email allaqachon mavjud.")
            return

        user = User(
            email=args.email,
            password_hash=hash_password(args.password),
            role=UserRole.admin,
            is_active=True,
            is_verified=True,
            hr_approved=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"OK: admin yaratildi — id={user.id}, email={user.email}")


if __name__ == "__main__":
    asyncio.run(main())
