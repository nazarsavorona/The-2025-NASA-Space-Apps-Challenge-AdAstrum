@echo off
REM View logs from running services

echo ==========================================
echo AdAstrum API Logs
echo ==========================================
echo.
echo Press Ctrl+C to exit
echo.

docker-compose logs -f api
