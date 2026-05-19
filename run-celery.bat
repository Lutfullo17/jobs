@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  echo venv topilmadi. Avval: python -m venv venv
  pause
  exit /b 1
)
if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
)
echo Celery worker (Windows: solo pool). Redis: docker compose up -d redis
set PYTHONUNBUFFERED=1
set REDIS_URL=redis://127.0.0.1:6500/0
.\venv\Scripts\python.exe -m celery -A app.core.celery_app.celery_app worker --loglevel=info -Q celery --pool=solo
