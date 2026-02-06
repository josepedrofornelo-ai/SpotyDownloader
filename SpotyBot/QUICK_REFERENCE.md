# 🎵 SpotyBot - Quick Reference Card

## 🚀 One-Line Quick Start

```bash
# macOS/Linux
python spotybot_gui.py

# Windows
python spotybot_gui.py
```

---

## 📦 Build Executable

| Platform | Command | Output |
|----------|---------|--------|
| **macOS** | `./build_app.sh` | `dist/SpotyBot.app` |
| **Linux** | `./build_app.sh` | `dist/SpotyBot/SpotyBot` |
| **Windows** | `build_app.bat` | `dist\SpotyBot\SpotyBot.exe` |

---

## ▶️ Launch Executable

| Platform | Command |
|----------|---------|
| **macOS** | `./launch_spotybot.sh` or double-click |
| **Linux** | `./launch_spotybot.sh` |
| **Windows** | `launch_spotybot.bat` or double-click |

---

## 🛠️ Common Tasks

### First-Time Setup

```bash
# 1. Clone/download project
git clone <repo-url>
cd SpotyBot

# 2. Create virtual environment
python -m venv .venv

# 3. Activate venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure Spotify API
cp .env.example .env
# Edit .env with your credentials
```

### Run GUI

```bash
# With Python
python spotybot_gui.py

# Or standalone
./launch_spotybot.sh      # macOS/Linux
launch_spotybot.bat        # Windows
```

### CLI Commands

```bash
# Download playlist
spotybot https://open.spotify.com/playlist/...

# Download with options
spotybot download --format flac --quality 320k <url>

# Search and download
spotybot search "Artist - Song Name"

# Interactive mode
spotybot interactive
```

### Build for Distribution

```bash
# Build
./build_app.sh           # macOS/Linux
build_app.bat           # Windows

# Create package
cd dist
zip -r SpotyBot-macOS.zip SpotyBot.app              # macOS
tar -czf SpotyBot-Linux.tar.gz SpotyBot/            # Linux
powershell Compress-Archive SpotyBot SpotyBot.zip   # Windows
```

---

## 🐛 Quick Troubleshooting

### Python Issues

```bash
# Check Python version
python --version  # Should be 3.10+

# Upgrade pip
pip install --upgrade pip

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Tkinter Issues

**macOS:**
```bash
brew install python-tk@3.13
rm -rf .venv && python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Linux Ubuntu/Debian:**
```bash
sudo apt install python3-tk
```

**Windows:**
- Reinstall Python from python.org

### App Won't Launch

**macOS Gatekeeper:**
```bash
xattr -cr dist/SpotyBot.app
```

**Linux Permissions:**
```bash
chmod +x dist/SpotyBot/SpotyBot
```

**Windows Defender:**
- Click "More info" → "Run anyway"

---

## 📝 File Locations

### Source Files
- **GUI:** `spotybot_gui.py`
- **Config:** `.env`
- **Modules:** `spotybot/`

### Build Files
- **macOS:** `dist/SpotyBot.app`
- **Linux:** `dist/SpotyBot/`
- **Windows:** `dist\SpotyBot\`

### Documentation
- **Main:** `README.md`
- **Installation:** `PLATFORM_INSTALL.md`
- **Executable:** `EXECUTABLE_README.md`
- **Summary:** `MULTIPLATFORM_SUMMARY.md`

---

## ⚙️ Default Settings

- **Format:** MP3
- **Quality:** 128k
- **Concurrent:** 8
- **Output:** `./downloads`
- **Metadata:** Enabled
- **Lyrics:** Disabled
- **Skip Existing:** Enabled

---

## 🔑 Spotify API

1. Go to: https://developer.spotify.com/dashboard
2. Create App
3. Copy Client ID & Client Secret
4. Add to `.env` or GUI settings

---

## 📊 Supported Formats

**Audio Formats:**
- MP3 (recommended)
- FLAC (lossless)
- OGG
- OPUS
- M4A

**Quality Options:**
- 96k, 128k, 160k, 192k, 256k, 320k

---

## 🌐 Supported URLs

✅ Playlists: `https://open.spotify.com/playlist/...`
✅ Albums: `https://open.spotify.com/album/...`
✅ Tracks: `https://open.spotify.com/track/...`
✅ Search: Just type song name

---

## 💾 Backup Important Files

Before updating or rebuilding:
```bash
# Backup settings
cp .env .env.backup

# Backup downloads
cp -r downloads downloads.backup
```

---

## 🔄 Update SpotyBot

```bash
# Pull latest changes
git pull

# Update dependencies
pip install --upgrade -r requirements.txt

# Rebuild executable
./build_app.sh  # or build_app.bat
```

---

## 📞 Get Help

1. Check `PLATFORM_INSTALL.md` for detailed setup
2. Check `EXECUTABLE_README.md` for build issues
3. Review troubleshooting sections
4. Open GitHub issue with:
   - Platform & Python version
   - Complete error message
   - Steps to reproduce

---

## ✨ Pro Tips

💡 Use virtual environments always
💡 Keep Python version between 3.10-3.13
💡 Save settings in GUI for convenience
💡 Use higher quality for better audio
💡 Enable "Skip Existing" to save time
💡 Limit concurrent downloads if slow
💡 Check output folder if files missing

---

## 🎯 Common Use Cases

### Download a playlist
1. Open GUI
2. Paste playlist URL
3. Click Download

### Change quality
1. Open GUI
2. Select quality dropdown
3. Choose desired quality
4. Save Settings (optional)

### Download to custom folder
1. Open GUI
2. Click "Browse"
3. Select folder
4. Click Download

### Build for friend
1. Run `./build_app.sh`
2. Zip the output
3. Send to friend
4. They extract and double-click

---

**Questions? Check the full documentation!**

📚 `README.md` - Overview & features
📋 `PLATFORM_INSTALL.md` - Setup guide
📦 `EXECUTABLE_README.md` - Build & distribution
📝 `MULTIPLATFORM_SUMMARY.md` - Technical details
