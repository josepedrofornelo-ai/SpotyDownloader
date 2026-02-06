@echo off
REM Build SpotyBot executable for Windows

echo 🔨 Building SpotyBot executable for Windows...
echo.

REM Check for virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found at .venv
    echo Please create one first: python -m venv .venv
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Build executable with PyInstaller
pyinstaller --name=SpotyBot ^
    --noconsole ^
    --onedir ^
    --add-data="spotybot;spotybot" ^
    --collect-data=pykakasi ^
    --collect-data=spotdl ^
    --collect-data=yt_dlp ^
    --hidden-import=tkinter ^
    --hidden-import=spotdl ^
    --hidden-import=spotipy ^
    --hidden-import=requests ^
    --hidden-import=dotenv ^
    --hidden-import=click ^
    --hidden-import=pydantic ^
    --hidden-import=rich ^
    --hidden-import=aiofiles ^
    --hidden-import=asyncio_throttle ^
    --noconfirm ^
    spotybot_gui.py

echo.
echo ✅ Build complete!
echo 📦 Executable: dist\SpotyBot\SpotyBot.exe
echo.
echo ▶️  To run: dist\SpotyBot\SpotyBot.exe
echo Or double-click: dist\SpotyBot\SpotyBot.exe

pause
