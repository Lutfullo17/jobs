from fastapi import FastAPI

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.support import router as support_router
from app.api.vacancies import router as vacancies_router
from app.core.config import settings


app = FastAPI(title=settings.app_name, debug=settings.debug)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(support_router)
app.include_router(vacancies_router)


@app.get("/")
async def root() -> dict:
    return {"message": "Jobify Auth API is running"}