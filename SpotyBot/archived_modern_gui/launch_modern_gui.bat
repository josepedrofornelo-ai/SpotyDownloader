@echo off
REM Launch script for SpotyBot Modern GUI (Windows)
REM This script activates the virtual environment and runs the modern GUI

echo 🎵 Launching SpotyBot Modern GUI...

REM Check if virtual environment exists
if not exist ".venv" (
    echo ❌ Virtual environment not found!
    echo Please run install.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if customtkinter is installed
python -c "import customtkinter" 2>nul
if errorlevel 1 (
    echo 📦 Installing modern GUI dependencies...
    pip install customtkinter pillow
)

REM Run the modern GUI
python spotybot_modern_gui.py

REM Deactivate virtual environment
call deactivate

pause
