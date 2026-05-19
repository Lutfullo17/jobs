@echo off
cd /d "%~dp0"
echo [1/3] WSL to'xtatilmoqda (Docker engine qayta tiklanadi)...
wsl --shutdown 2>nul

echo [2/3] Docker Desktop qayta ishga tushirilmoqda...
taskkill /IM "Docker Desktop.exe" /F 2>nul
timeout /t 3 /nobreak >nul
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

echo [3/3] Docker tayyor bo'lishini kutamiz (60 soniya)...
timeout /t 60 /nobreak >nul

docker version >nul 2>&1
if errorlevel 1 (
  echo Docker hali tayyor emas. Docker Desktop oynasida "Engine running" bo'lguncha kuting, keyin docker-up.bat ni qayta ishga tushiring.
) else (
  echo Docker ishlayapti. Endi docker-up.bat ni ishga tushiring.
)
pause
