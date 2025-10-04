@echo off
REM Start development environment

echo ==========================================
echo Starting AdAstrum API
echo ==========================================
echo.

docker-compose up -d

if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo API Server Started!
    echo ==========================================
    echo.
    echo Access points:
    echo   API:  http://localhost:8000
    echo   Docs: http://localhost:8000/docs
    echo.
    echo To view logs: logs.bat
    echo To test API: test-api.bat
    echo To stop: stop-dev.bat
    echo.
) else (
    echo.
    echo ==========================================
    echo Failed to start services!
    echo ==========================================
    echo.
    echo Please check:
    echo   1. Docker Desktop is running
    echo   2. No other service is using port 8000
    echo   3. Run: docker-compose logs
    echo.
)

pause
