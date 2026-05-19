from contextlib import asynccontextmanager
import sys

from fastapi import FastAPI

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.candidate_platform import router as candidate_platform_router
from app.api.candidate_vacancies import router as candidate_vacancies_router
from app.api.candidate_profile import router as candidate_profile_router
from app.api.candidate_recruitment import router as candidate_recruitment_router
from app.api.companies import router as companies_router
from app.api.hr import router as hr_router
from app.api.support import router as support_router
from app.api.vacancies import router as vacancies_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    sys.stderr.write(
        "\n[Jobify] Tasdiqlash kodi har doim chiqadi: [VERIFICATION-CODE] (register/resend dan keyin). "
        "Faqat Docker API: `docker compose logs -f app`.\n\n"
    )
    sys.stderr.flush()
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(support_router)
app.include_router(hr_router)
app.include_router(candidate_recruitment_router)
app.include_router(candidate_profile_router)
app.include_router(candidate_platform_router)
app.include_router(candidate_vacancies_router)
app.include_router(companies_router)
app.include_router(vacancies_router)


@app.get("/")
async def root() -> dict:
    return {
        "message": "Jobify API is running",
        "modules": ["auth", "admin", "hr", "vacancies", "companies", "support", "candidate", "profile"],
    }