#!/bin/bash
# Quick launcher for SpotyBot GUI

echo "🎵 Launching SpotyBot GUI..."

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python is not installed or not in PATH"
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Check if spotybot_gui.py exists
if [ ! -f "spotybot_gui.py" ]; then
    echo "❌ spotybot_gui.py not found in current directory"
    echo "Please run this from the SpotyBot folder"
    exit 1
fi

# Run the GUI
$PYTHON_CMD spotybot_gui.py
