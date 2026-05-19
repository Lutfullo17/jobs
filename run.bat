@echo off
cd /d "%~dp0"
REM Docker + lokal API birgalikda: run-with-docker.bat
if not exist "venv\Scripts\python.exe" (
  echo venv topilmadi. Avval: python -m venv venv
  pause
  exit /b 1
)
if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
)
echo Uvicorn: http://127.0.0.1:8001/docs  (Ctrl+C to'xtatish)
echo DB/Redis Dockerda bo'lsa: docker compose up -d db redis celery-worker
set PYTHONUNBUFFERED=1
set DATABASE_URL=postgresql+asyncpg://postgres:123@127.0.0.1:5432/jobify
set REDIS_URL=redis://127.0.0.1:6500/0
.\venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8001
