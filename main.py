from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.core.config import settings


app = FastAPI(title=settings.app_name, debug=settings.debug)
app.include_router(auth_router)


@app.get("/")
async def root() -> dict:
    return {"message": "Jobify Auth API is running"}