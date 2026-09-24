# Archived Modern GUI

This folder contains the modern GUI version of SpotyBot that was built with CustomTkinter.

## What's Inside

- `spotybot_modern_gui.py` - Modern GUI application with CustomTkinter
- `launch_modern_gui.sh` - macOS/Linux launcher for modern GUI
- `launch_modern_gui.bat` - Windows launcher for modern GUI
- `MODERN_GUI_README.md` - Detailed documentation for the modern GUI
- `QUICK_START_MODERN.md` - Quick start guide for the modern GUI
- `GUI_COMPARISON.md` - Comparison between classic and modern GUIs
- `VISUAL_SHOWCASE.md` - Visual tour of the modern GUI

## Why Archived?

The classic Tkinter GUI (`spotybot_gui.py`) has been chosen as the default interface because:
- It has fewer dependencies (no need for CustomTkinter)
- It's lighter and faster to start
- It's more compatible across different systems
- It provides all essential functionality

## Using the Modern GUI

If you prefer the modern interface with its enhanced design, you can still use it:

### Requirements

The modern GUI requires additional dependencies:
```bash
pip install customtkinter pillow
```

### Launching

**From the main directory:**
```bash
# macOS/Linux
./archived_modern_gui/launch_modern_gui.sh

# Windows
archived_modern_gui\launch_modern_gui.bat

# Or directly with Python
python archived_modern_gui/spotybot_modern_gui.py
```

## Features

The modern GUI includes:
- Dark/Light theme toggle
- Modern card-based design
- Download queue management
- Download history with statistics
- Multi-page navigation
- Enhanced visual feedback

For full feature details, see [MODERN_GUI_README.md](MODERN_GUI_README.md).

---

**Note:** Both GUIs work with the same backend and can coexist. Your settings and downloads work with either interface.
