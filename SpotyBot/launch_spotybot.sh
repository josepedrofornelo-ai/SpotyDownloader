#!/bin/bash
# Quick launcher for SpotyBot standalone app - Cross-platform

echo "🎵 Launching SpotyBot..."

# Detect platform
OS_TYPE=$(uname -s)

case "$OS_TYPE" in
    Darwin*)
        # macOS
        if [ ! -d "dist/SpotyBot.app" ]; then
            echo "❌ SpotyBot.app not found. Run ./build_app.sh first"
            exit 1
        fi
        open dist/SpotyBot.app
        ;;
    Linux*)
        # Linux
        if [ ! -f "dist/SpotyBot/SpotyBot" ]; then
            echo "❌ SpotyBot executable not found. Run ./build_app.sh first"
            exit 1
        fi
        ./dist/SpotyBot/SpotyBot &
        ;;
    *)
        echo "❌ Unsupported platform: $OS_TYPE"
        exit 1
        ;;
esac

echo "✅ SpotyBot launched successfully!"
