@echo off
title SpotyBot GUI Launcher

echo.
echo  🎵 Starting SpotyBot GUI...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if spotybot_gui.py exists
if not exist "spotybot_gui.py" (
    echo ❌ spotybot_gui.py not found in current directory
    echo Please run this from the SpotyBot folder
    pause
    exit /b 1
)

REM Run the GUI
python spotybot_gui.py

REM Keep window open if there's an error
if %errorlevel% neq 0 (
    echo.
    echo ❌ Error launching GUI
    pause
)
