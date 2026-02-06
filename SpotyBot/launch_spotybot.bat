@echo off
REM Quick launcher for SpotyBot on Windows

echo 🎵 Launching SpotyBot...
echo.

REM Check if executable exists
if not exist "dist\SpotyBot\SpotyBot.exe" (
    echo ❌ SpotyBot.exe not found!
    echo Please run build_app.bat first to create the executable.
    echo.
    pause
    exit /b 1
)

REM Launch the executable
start "" "dist\SpotyBot\SpotyBot.exe"

echo ✅ SpotyBot launched successfully!
