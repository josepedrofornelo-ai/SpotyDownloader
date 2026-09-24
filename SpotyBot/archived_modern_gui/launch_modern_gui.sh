#!/bin/bash

# Launch script for SpotyBot Modern GUI
# This script activates the virtual environment and runs the modern GUI

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🎵 Launching SpotyBot Modern GUI..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run install.sh or install.bat first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if customtkinter is installed
python -c "import customtkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing modern GUI dependencies..."
    pip install customtkinter pillow
fi

# Run the modern GUI
python spotybot_modern_gui.py

# Deactivate virtual environment
deactivate
