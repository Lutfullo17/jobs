@echo off
cd /d "%~dp0"

if not exist ".env" (
  echo .env topilmadi — .env.example dan nusxa olinmoqda...
  copy /Y ".env.example" ".env" >nul
)

echo Docker stack ishga tushirilmoqda (build + migratsiya)...
docker compose up --build -d
if errorlevel 1 (
  echo.
  echo XATO: Docker javob bermadi. docker-reset.bat ni ishga tushiring yoki Docker Desktop ochilganini tekshiring.
  pause
  exit /b 1
)

echo.
echo Tayyor:
echo   Swagger:  http://127.0.0.1:8001/docs
echo   Loglar:   logs-app.bat  yoki  docker compose logs -f app
echo   Kod:      docker compose logs -f app  ichida [VERIFICATION-CODE]
echo.
pause
