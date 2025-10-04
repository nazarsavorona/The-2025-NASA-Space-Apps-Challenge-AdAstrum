@echo off
REM Stop development environment

echo ==========================================
echo Stopping AdAstrum API
echo ==========================================
echo.

docker-compose down

if %errorlevel% equ 0 (
    echo.
    echo Services stopped successfully!
) else (
    echo.
    echo Failed to stop services!
)

echo.
pause
