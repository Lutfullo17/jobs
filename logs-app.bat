@echo off
cd /d "%~dp0"
start "Jobify API — docker logs" cmd /k "docker compose logs -f app"
