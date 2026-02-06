# Platform-Specific Installation Guide

This guide provides detailed installation instructions for SpotyBot on **Windows**, **macOS**, and **Linux**.

---

## 🪟 Windows Installation

### Prerequisites

1. **Python 3.10 or later** (3.13 recommended)
   - Download from: https://www.python.org/downloads/
   - ✅ Check "Add Python to PATH" during installation

2. **Git** (optional, for cloning)
   - Download from: https://git-scm.com/download/win

### Installation Steps

1. **Clone or Download the Repository:**
   ```cmd
   git clone https://github.com/yourusername/SpotyBot.git
   cd SpotyBot
   ```
   
   Or download ZIP and extract it.

2. **Create Virtual Environment:**
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Configure Spotify API:**
   - Copy `.env.example` to `.env`
   - Add your Spotify API credentials

5. **Run the GUI:**
   ```cmd
   python spotybot_gui.py
   ```

### Building Standalone Executable

```cmd
build_app.bat
```

The executable will be created at: `dist\SpotyBot\SpotyBot.exe`

### Troubleshooting Windows

**Issue:** `'python' is not recognized`
- **Solution:** Install Python and ensure "Add Python to PATH" was checked

**Issue:** `No module named 'tkinter'`
- **Solution:** Reinstall Python from python.org (includes tkinter)

**Issue:** Windows Defender blocks the exe
- **Solution:** Click "More info" → "Run anyway"

---

## 🍎 macOS Installation

### Prerequisites

1. **Python 3.10 or later** (3.13 recommended)
   - Install via Homebrew (recommended):
     ```bash
     brew install python@3.13
     ```
   - Or download from: https://www.python.org/downloads/

2. **tkinter support:**
   ```bash
   brew install python-tk@3.13
   # Or for Python 3.14:
   brew install python-tk@3.14
   ```

3. **Xcode Command Line Tools:**
   ```bash
   xcode-select --install
   ```

### Installation Steps

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/SpotyBot.git
   cd SpotyBot
   ```

2. **Create Virtual Environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   If using Python 3.14:
   ```bash
   pip install --ignore-requires-python -r requirements.txt
   ```

4. **Configure Spotify API:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Run the GUI:**
   ```bash
   python spotybot_gui.py
   ```

### Building Standalone App

```bash
chmod +x build_app.sh
./build_app.sh
```

The app will be created at: `dist/SpotyBot.app`

**Launch:**
```bash
open dist/SpotyBot.app
# Or use the launcher:
./launch_spotybot.sh
```

### Troubleshooting macOS

**Issue:** `ModuleNotFoundError: No module named '_tkinter'`
- **Solution:** 
  ```bash
  brew install python-tk@3.13  # or @3.14
  # Recreate venv:
  rm -rf .venv
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

**Issue:** macOS blocks the app (Gatekeeper)
- **Solution:** 
  ```bash
  xattr -cr dist/SpotyBot.app
  # Or: Right-click → Open → Click "Open"
  ```

**Issue:** spotdl version incompatible with Python 3.14
- **Solution:** 
  ```bash
  pip install --ignore-requires-python -r requirements.txt
  ```

---

## 🐧 Linux Installation

### Prerequisites

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv python3-tk git
```

**Fedora:**
```bash
sudo dnf install python3 python3-pip python3-tkinter git
```

**Arch:**
```bash
sudo pacman -S python python-pip tk git
```

### Installation Steps

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/SpotyBot.git
   cd SpotyBot
   ```

2. **Create Virtual Environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Spotify API:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials using nano or vim
   nano .env
   ```

5. **Run the GUI:**
   ```bash
   python spotybot_gui.py
   ```

### Building Standalone Executable

```bash
chmod +x build_app.sh
./build_app.sh
```

The executable will be created at: `dist/SpotyBot/SpotyBot`

**Launch:**
```bash
./dist/SpotyBot/SpotyBot
# Or use the launcher:
./launch_spotybot.sh
```

### Troubleshooting Linux

**Issue:** `ModuleNotFoundError: No module named 'tkinter'`
- **Ubuntu/Debian:** `sudo apt install python3-tk`
- **Fedora:** `sudo dnf install python3-tkinter`
- **Arch:** `sudo pacman -S tk`

**Issue:** Permission denied when running executable
- **Solution:**
  ```bash
  chmod +x dist/SpotyBot/SpotyBot
  ```

**Issue:** Display server issues
- **Solution:** Ensure X11 or Wayland is running properly

---

## 📦 Virtual Environment Best Practices

### Why Use Virtual Environments?

- ✅ Isolates project dependencies
- ✅ Prevents version conflicts
- ✅ Makes projects reproducible
- ✅ Required for PyInstaller builds

### Creating a Virtual Environment

**All Platforms:**
```bash
python -m venv .venv
# Or on some systems:
python3 -m venv .venv
```

### Activating the Virtual Environment

**Windows:**
```cmd
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### Deactivating

**All Platforms:**
```bash
deactivate
```

---

## 🔑 Spotify API Setup

### Getting Your API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **"Create an App"**
4. Fill in:
   - **App name:** "SpotyBot" (or any name)
   - **App description:** "Personal music downloader"
   - **Redirect URI:** http://localhost:8888/callback
5. Accept terms and click **"Create"**
6. Click **"Settings"**
7. Copy your:
   - **Client ID**
   - **Client Secret** (click "View client secret")

### Adding Credentials to SpotyBot

**Option 1: GUI Settings (Easiest)**
1. Run the GUI: `python spotybot_gui.py`
2. Enter your credentials in the settings
3. Click "Save Settings"

**Option 2: Manual .env File**
1. Copy the example file:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env`:
   ```env
   SPOTIFY_CLIENT_ID=your_client_id_here
   SPOTIFY_CLIENT_SECRET=your_client_secret_here
   ```

---

## 🔧 Common Dependencies

### Required Python Packages

All installed automatically via `requirements.txt`:
- **spotdl** - Core download functionality
- **spotipy** - Spotify API client
- **requests** - HTTP library
- **python-dotenv** - Environment variable management
- **click** - CLI framework
- **pydantic** - Configuration management
- **rich** - Terminal formatting
- **aiofiles** - Async file operations
- **asyncio-throttle** - Rate limiting

### System Dependencies

**macOS:**
- Xcode Command Line Tools
- Homebrew (recommended)
- python-tk

**Linux:**
- python3-tk or python-tkinter
- python3-dev (for building)
- ffmpeg (optional, for better audio processing)

**Windows:**
- Visual C++ Redistributable (usually included with Python)

---

## 🚀 Quick Platform Comparison

| Feature | Windows | macOS | Linux |
|---------|---------|-------|-------|
| Python Install | python.org | Homebrew | apt/dnf/pacman |
| Tkinter | Included | Separate pkg | Separate pkg |
| Build Output | .exe | .app | executable |
| Typical Issues | Defender warnings | Gatekeeper | Permissions |
| Best Python Ver | 3.11-3.13 | 3.11-3.13 | 3.10-3.13 |

---

## 💡 Tips

1. **Always use a virtual environment** - Prevents conflicts
2. **Keep Python updated** - But avoid bleeding edge (3.14+)
3. **Check Python version:**
   ```bash
   python --version  # or python3 --version
   ```
4. **Upgrade pip before installing:**
   ```bash
   pip install --upgrade pip
   ```
5. **Clean install if issues persist:**
   ```bash
   rm -rf .venv build dist
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

---

## 🆘 Getting Help

If you encounter issues:

1. Check the [Troubleshooting section](#troubleshooting) for your platform
2. Review [EXECUTABLE_README.md](EXECUTABLE_README.md) for build issues
3. Ensure all prerequisites are installed
4. Try a clean virtual environment
5. Check Python version compatibility
6. Open an issue on GitHub with:
   - Your platform and Python version
   - Complete error message
   - Steps to reproduce

---

## ✅ Installation Checklist

- [ ] Python 3.10+ installed
- [ ] Tkinter support available
- [ ] Git installed (optional)
- [ ] Repository cloned/downloaded
- [ ] Virtual environment created
- [ ] Dependencies installed successfully
- [ ] Spotify API credentials configured
- [ ] GUI launches successfully
- [ ] Test download works

Happy downloading! 🎵
