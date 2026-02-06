# SpotyBot - Standalone Application (Cross-Platform)

## 🎉 Your executable is ready!

SpotyBot can be built as a standalone application for **Windows**, **macOS**, and **Linux**.

---

## 🏗️ Building the Application

### **macOS / Linux**
```bash
./build_app.sh
```

### **Windows**
```cmd
build_app.bat
```

Or use PowerShell:
```powershell
.\build_app.bat
```

---

## 📦 Output Locations

### **macOS**
- **Location:** `dist/SpotyBot.app`
- **Type:** Application Bundle (.app)
- **Size:** ~60-70 MB

### **Linux**
- **Location:** `dist/SpotyBot/SpotyBot`
- **Type:** Executable folder
- **Size:** ~60-70 MB

### **Windows**
- **Location:** `dist\SpotyBot\SpotyBot.exe`
- **Type:** Executable folder
- **Size:** ~60-70 MB

---

## 🚀 Running the Application

### **Quick Launch**

**macOS / Linux:**
```bash
./launch_spotybot.sh
```

**Windows:**
```cmd
launch_spotybot.bat
```

### **Manual Launch**

**macOS:**
```bash
open dist/SpotyBot.app
# Or double-click SpotyBot.app in Finder
```

**Linux:**
```bash
./dist/SpotyBot/SpotyBot
# Make executable if needed:
chmod +x dist/SpotyBot/SpotyBot
```

**Windows:**
```cmd
dist\SpotyBot\SpotyBot.exe
REM Or double-click SpotyBot.exe in Explorer
```

---

## 📤 Distribution

### **Creating Distribution Packages**

**macOS:**
```bash
cd dist
zip -r SpotyBot-macOS.zip SpotyBot.app
```

**Linux:**
```bash
cd dist
tar -czf SpotyBot-Linux.tar.gz SpotyBot/
```

**Windows:**
```cmd
cd dist
powershell Compress-Archive -Path SpotyBot -DestinationPath SpotyBot-Windows.zip
```

### **Sharing the App**

Recipients can:
1. Extract the archive
2. Run the executable directly
3. **No Python or dependencies needed!**

---

## ⚠️ Platform-Specific Notes

### **macOS Security**

First-time launch may be blocked by Gatekeeper:
1. Right-click on `SpotyBot.app` → Select "Open"
2. Click "Open" in the security dialog

**Or via terminal:**
```bash
xattr -cr dist/SpotyBot.app
```

### **Windows Security**

Windows Defender may flag the app as unknown:
1. Click "More info"
2. Click "Run anyway"

To avoid warnings, consider code signing (requires certificate).

### **Linux Permissions**

Make sure the executable has proper permissions:
```bash
chmod +x dist/SpotyBot/SpotyBot
```

---

## ✨ Features

The standalone app includes:
- ✅ All Python dependencies bundled
- ✅ No need for Python installation
- ✅ No need to activate virtual environments
- ✅ Complete GUI interface
- ✅ Spotify playlist, album, and track downloads
- ✅ Auto-detects URLs vs search queries
- ✅ Configurable quality and format settings

---

## 🔧 Requirements

### **Build Requirements**

**All Platforms:**
- Python 3.10+ (3.13 recommended, 3.14 works with `--ignore-requires-python`)
- Virtual environment with dependencies installed
- PyInstaller (installed automatically with requirements)

**macOS:**
- Xcode Command Line Tools
- `python-tk` (install via `brew install python-tk@3.14`)

**Linux:**
- `python3-tk` package
- Development headers: `sudo apt install python3-dev` (Ubuntu/Debian)

**Windows:**
- Python from python.org (includes tkinter)
- Visual C++ Build Tools (for some dependencies)

### **Runtime Requirements**

**Built executables require:**
- **macOS:** 10.13+ (for ARM builds: macOS 11.0+)
- **Linux:** Modern distribution with GUI support
- **Windows:** Windows 10/11 (64-bit)

---

## 🐛 Troubleshooting

### **Build Fails**

1. **Check Python version:**
   ```bash
   python --version  # or python3 --version
   ```

2. **Reinstall dependencies:**
   ```bash
   pip install --upgrade -r requirements.txt
   pip install --upgrade pyinstaller
   ```

3. **Clean build:**
   ```bash
   rm -rf build dist *.spec
   ./build_app.sh
   ```

### **App Won't Launch**

1. **Check for errors:**
   - **macOS:** `./dist/SpotyBot.app/Contents/MacOS/SpotyBot`
   - **Linux:** `./dist/SpotyBot/SpotyBot`
   - **Windows:** Run from cmd.exe to see error messages

2. **Missing data files:** Rebuild with `--collect-data` flags

3. **Permission issues (Linux/macOS):**
   ```bash
   chmod +x dist/SpotyBot/SpotyBot
   ```

---

## 📊 Platform Comparison

| Feature | macOS | Linux | Windows |
|---------|-------|-------|---------|
| Bundle Type | .app | Folder | Folder (.exe) |
| Size | ~60MB | ~60MB | ~70MB |
| GUI | Native | X11/Wayland | Native |
| Distribution | .app or .dmg | .tar.gz / .deb | .zip / installer |
| Code Signing | Optional | Not needed | Optional |

---

## 🔄 Rebuilding

After making changes to the code:

```bash
# macOS/Linux
./build_app.sh

# Windows
build_app.bat
```

The script will automatically:
- Detect your platform
- Use correct build options
- Bundle all dependencies
- Create platform-appropriate executable

---

## 🎵 Enjoy!

Your SpotyBot is now a fully standalone, cross-platform application!
