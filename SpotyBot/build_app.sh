#!/bin/bash
# Build SpotyBot executable - Cross-platform

echo "🔨 Building SpotyBot executable..."
echo "🖥️  Platform: $(uname -s)"

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
else
    echo "❌ Virtual environment not found. Please create one first."
    exit 1
fi

# Detect platform and set appropriate options
OS_TYPE=$(uname -s)
case "$OS_TYPE" in
    Darwin*)
        echo "🍎 Building for macOS..."
        PLATFORM_ARGS="--windowed"
        ;;
    Linux*)
        echo "🐧 Building for Linux..."
        PLATFORM_ARGS="--noconsole"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        echo "🪟 Building for Windows..."
        PLATFORM_ARGS="--noconsole --icon=NONE"
        ;;
    *)
        echo "🖥️  Building for unknown platform, using default settings..."
        PLATFORM_ARGS=""
        ;;
esac

# Set data separator based on platform
if [[ "$OS_TYPE" == "MINGW"* ]] || [[ "$OS_TYPE" == "MSYS"* ]] || [[ "$OS_TYPE" == "CYGWIN"* ]]; then
    DATA_SEP=";"
else
    DATA_SEP=":"
fi

# Build executable with PyInstaller
pyinstaller --name="SpotyBot" \
    $PLATFORM_ARGS \
    --onedir \
    --add-data="spotybot${DATA_SEP}spotybot" \
    --collect-data=pykakasi \
    --collect-data=spotdl \
    --collect-data=yt_dlp \
    --hidden-import=tkinter \
    --hidden-import=spotdl \
    --hidden-import=spotipy \
    --hidden-import=requests \
    --hidden-import=dotenv \
    --hidden-import=click \
    --hidden-import=pydantic \
    --hidden-import=rich \
    --hidden-import=aiofiles \
    --hidden-import=asyncio_throttle \
    --noconfirm \
    spotybot_gui.py

echo ""
echo "✅ Build complete!"
echo ""

# Platform-specific instructions
case "$OS_TYPE" in
    Darwin*)
        echo "📦 Application bundle: dist/SpotyBot.app"
        echo "▶️  Run: open dist/SpotyBot.app"
        echo "   Or: ./dist/SpotyBot.app/Contents/MacOS/SpotyBot"
        ;;
    Linux*)
        echo "📦 Executable: dist/SpotyBot/SpotyBot"
        echo "▶️  Run: ./dist/SpotyBot/SpotyBot"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        echo "📦 Executable: dist/SpotyBot/SpotyBot.exe"
        echo "▶️  Run: dist\\SpotyBot\\SpotyBot.exe"
        ;;
    *)
        echo "📦 Location: dist/SpotyBot/"
        echo "▶️  Check dist/ folder for executables"
        ;;
esac
