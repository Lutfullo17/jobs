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



echo [1/4] Docker stack (db, redis, celery-worker, migratsiya)...

docker compose up -d db redis celery-worker

if errorlevel 1 (

  echo Docker xato. docker-reset.bat yoki Docker Desktop ni tekshiring.

  pause

  exit /b 1

)



echo [2/4] 12 soniya kutamiz (Postgres + migratsiya)...

docker compose run --rm app alembic upgrade head 2>nul

timeout /t 8 /nobreak >nul



echo [3/4] Docker app konteyneri to'xtatiladi — port 8001 lokal API uchun

docker compose stop app 2>nul



echo [4/4] Lokal API: http://127.0.0.1:8001/docs

echo Kod shu oynada: [VERIFICATION-CODE]  (celery: docker compose logs -f celery-worker)

echo.

set PYTHONUNBUFFERED=1

set DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/jobify

set REDIS_URL=redis://127.0.0.1:6500/0

.\venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8001

