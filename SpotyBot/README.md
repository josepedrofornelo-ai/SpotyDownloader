# 🎵 SpotyBot - Spotify Playlist Downloader

A powerful and user-friendly Spotify playlist downloader with **GUI and CLI** interfaces that uses **spotDL** to find and download songs from YouTube Music with full metadata support.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

## ✨ Features

- 🎨 **Graphical User Interface (GUI)** - Easy-to-use Tkinter interface
- 💻 **Command Line Interface (CLI)** - Powerful terminal commands
- 📦 **Standalone Executables** - No Python installation required
- 🎵 **Download entire Spotify playlists, albums, or individual tracks**
- 🔍 **Search and download songs by name**
- 🎨 **Rich progress bars and status updates**
- ⚡ **Async downloads with configurable concurrency**
- 📁 **Customizable output directory and file naming**
- 🎼 **Full metadata embedding (title, artist, album, cover art, lyrics)**
- 📊 **Multiple audio formats and quality options**
- 🔄 **Skip existing files to avoid re-downloading**
- 🌐 **Interactive mode for easy use**
- ⚙️ **Configurable via environment variables or config files**

## 🚀 Quick Start

### Option 1: Use the GUI (Easiest)

**With Python:**
```bash
# Install dependencies
pip install -r requirements.txt

# Launch the GUI
python spotybot_gui.py
```

**Standalone Executable (No Python needed):**

Download the pre-built executable for your platform:
- **Windows:** `SpotyBot-Windows.zip`
- **macOS:** `SpotyBot-macOS.zip`
- **Linux:** `SpotyBot-Linux.tar.gz`

Extract and double-click to run!

### Option 2: Command Line

```bash
# Clone the repository
git clone https://github.com/spotybot/spotybot.git
cd spotybot

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### 2. Setup Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Copy your **Client ID** and **Client Secret**

### 3. Configure SpotyBot

Run the setup wizard:

```bash
spotybot setup
Or manually create a `.env` file:

```bash
cp .env.example .env
# Edit .env with your Spotify credentials
```

## 📦 Building Standalone Executables

Create standalone applications that don't require Python:

### **macOS / Linux**
```bash
# Install dependencies (if not already done)
pip install -r requirements.txt

# Build the executable
./build_app.sh

# Launch the app
./launch_spotybot.sh
```

### **Windows**
```cmd
REM Install dependencies (if not already done)
pip install -r requirements.txt

REM Build the executable
build_app.bat

REM Launch the app
launch_spotybot.bat
```

**Output locations:**
- **macOS:** `dist/SpotyBot.app`
- **Linux:** `dist/SpotyBot/SpotyBot`
- **Windows:** `dist\SpotyBot\SpotyBot.exe`

See [EXECUTABLE_README.md](EXECUTABLE_README.md) for detailed instructions on building, distributing, and platform-specific notes.

### 4. Start Downloading! 🎉

**With GUI:**
```bash
python spotybot_gui.py
# Or run the standalone executable
```

**With CLI:**
```bash
# Interactive mode (recommended for beginners)
spotybot interactive

# Download a playlist directly
spotybot https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M

# Download with specific options
spotybot download --format flac --quality 320k <playlist_url>

# Search and download
spotybot search "The Beatles Hey Jude"
```

## 📖 Usage

### Graphical User Interface (GUI)

Launch the GUI for the easiest experience:

```bash
python spotybot_gui.py
```

**GUI Features:**
- 🎯 **Auto-detects** playlist, album, or track URLs
- 📁 **Browse** for download folder
- ⚙️ **Configure** all settings visually:
  - Audio quality (96k - 320k)
  - Audio format (MP3, FLAC, OGG, OPUS, M4A)
  - Concurrent downloads (1-12)
  - Metadata embedding
  - Lyrics download
  - Skip existing files
  - Max tracks limit
- 📊 **Real-time progress** updates
- 💾 **Save settings** to .env file
- 🔄 **Reset to defaults** with one click
- ℹ️ **Built-in help** system

**Standalone GUI:**
If you built or downloaded the standalone executable, just double-click:
- **macOS:** `SpotyBot.app`
- **Linux:** `SpotyBot` executable
- **Windows:** `SpotyBot.exe`

### Command Line Interface

#### Basic Commands

```bash
# Download any Spotify URL (auto-detects playlist/album/track)
spotybot <spotify_url>

# Download specific types
spotybot playlist <playlist_url>
spotybot album <album_url>
spotybot track <track_url>

# Search and download
spotybot search "artist - song name"
spotybot search "The Beatles Hey Jude" --limit 3

# Interactive mode
spotybot interactive

# Show current configuration
spotybot config-info
```

#### Options

```bash
spotybot [OPTIONS] COMMAND [ARGS]...

Options:
  -c, --config PATH              Configuration file path
  -o, --output PATH              Output directory for downloads
  -f, --format [mp3|flac|ogg|opus|m4a]  Audio format
  -q, --quality [96k|128k|160k|192k|256k|320k]  Audio quality
  --async / --no-async           Use async downloads (default: True)
  -j, --max-concurrent INTEGER   Maximum concurrent downloads
  -v, --verbose                  Enable verbose logging
  --quiet                        Quiet mode - minimal output
  --version                      Show the version and exit
  --help                         Show help message
```

### Interactive Mode

The interactive mode provides a user-friendly interface:

```bash
spotybot interactive
```

Features:
- 🎵 Paste any Spotify URL to start downloading
- 🔍 Search for songs by typing search queries
- ⚙️ View current configuration
- 📖 Built-in help system

### Python API

You can also use SpotyBot programmatically:

```python
from spotybot import SpotyBot, Config

# Create configuration
config = Config.from_env()

# Initialize bot
bot = SpotyBot(config)

# Download a playlist
playlist_info, results = bot.download_playlist(
    "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
)

# Check results
successful = [r for r in results if r.success]
print(f"Downloaded {len(successful)} tracks successfully!")
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required - Spotify API Credentials
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here

# Optional - Download Settings
DOWNLOAD_FORMAT=mp3                    # mp3, flac, ogg, opus, m4a
DOWNLOAD_QUALITY=320k                  # 96k, 128k, 160k, 192k, 256k, 320k
OUTPUT_TEMPLATE="{artists} - {title}.{output-ext}"
OUTPUT_DIRECTORY=./downloads

# Optional - Behavior
MAX_CONCURRENT_DOWNLOADS=4
SKIP_EXISTING_FILES=true
EMBED_METADATA=true
DOWNLOAD_LYRICS=true
AUDIO_PROVIDER=youtube-music           # youtube-music, youtube, soundcloud
```

### Output Template Variables

Customize your file naming with these variables:

- `{title}` - Song title
- `{artists}` - All artists (joined with &)
- `{artist}` - Main artist
- `{album}` - Album name
- `{album-artist}` - Album artist
- `{year}` - Release year
- `{track-number}` - Track number
- `{disc-number}` - Disc number
- `{output-ext}` - File extension

Example: `"{artists} - {title} ({year}).{output-ext}"`
Result: `"The Beatles - Hey Jude (1968).mp3"`

## 🎯 Examples

### Download Spotify Playlists

```bash
# Download a public playlist
spotybot https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M

# Download only first 10 tracks
spotybot playlist <playlist_url> --max-tracks 10

# Get playlist info without downloading
spotybot playlist <playlist_url> --info-only
```

### Download Albums

```bash
# Download complete album
spotybot https://open.spotify.com/album/1DFixLWuPkv3KT3TnV35m3

# Using album command
spotybot album https://open.spotify.com/album/1DFixLWuPkv3KT3TnV35m3
```

### Download Individual Tracks

```bash
# Download single track
spotybot https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh

# Using track command
spotybot track https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh
```

### Search and Download

```bash
# Search for a specific song
spotybot search "Bohemian Rhapsody Queen"

# Download multiple search results
spotybot search "The Beatles" --limit 5

# Interactive search in interactive mode
SpotyBot> search led zeppelin stairway to heaven
```

### Advanced Usage

```bash
# High-quality FLAC downloads
spotybot --format flac --quality 320k <url>

# Custom output directory
spotybot --output ./my-music <url>

# Quiet mode for scripting
spotybot --quiet <url>

# Maximum concurrent downloads
spotybot --max-concurrent 8 <url>

# Synchronous downloads (no async)
spotybot --no-async <url>
```

## 🔧 Installation & Requirements

### Prerequisites

- **Python 3.8 or higher**
- **FFmpeg** (for audio conversion)
  - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg` or equivalent

### Installation Methods

#### Method 1: From Source (Recommended)

```bash
git clone https://github.com/spotybot/spotybot.git
cd spotybot
pip install -r requirements.txt
pip install -e .
```

#### Method 2: Direct Install

```bash
pip install git+https://github.com/spotybot/spotybot.git
```

#### Method 3: Development Install

```bash
git clone https://github.com/spotybot/spotybot.git
cd spotybot
pip install -e .[dev]
```

### Verify Installation

```bash
spotybot --version
spotybot --help
```

## 🔍 How It Works

SpotyBot combines the power of two excellent libraries:

1. **Spotipy** - Accesses Spotify's Web API to fetch playlist/track metadata
2. **spotDL** - Finds and downloads corresponding audio from YouTube Music

The process:
1. 🔗 Parse Spotify URL and authenticate with Spotify API
2. 📋 Fetch track metadata (title, artist, album, etc.)
3. 🔍 Use spotDL to search for matching audio on YouTube Music
4. ⬇️ Download audio with best quality match
5. 🎵 Embed metadata and album art into the audio file
6. 📁 Save to your specified output directory

## ❓ Troubleshooting

### Common Issues

**"Spotify credentials not configured"**
- Ensure your `.env` file exists with valid `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`
- Run `spotybot setup` for guided configuration

**"FFmpeg not found"**
- Install FFmpeg for your operating system
- Ensure `ffmpeg` is in your system PATH

**"No tracks found" or download failures**
- Some tracks may not be available on YouTube Music
- Try different audio providers: `AUDIO_PROVIDER=youtube`
- Check your internet connection

**Permission errors on Windows**
- Run Command Prompt as Administrator
- Check output directory write permissions

**Slow downloads**
- Increase concurrent downloads: `--max-concurrent 8`
- Use async mode: `--async` (default)
- Check your internet speed

### Debug Mode

Enable detailed logging:

```bash
spotybot --verbose <url>
# or set environment variable
LOG_LEVEL=DEBUG spotybot <url>
```

### Reset Configuration

```bash
rm .env
spotybot setup
```

## 🤝 Contributing

Contributions are welcome! Please feel free to:

1. 🐛 Report bugs
2. 💡 Suggest features
3. 🔧 Submit pull requests
4. 📖 Improve documentation

### Development Setup

```bash
git clone https://github.com/spotybot/spotybot.git
cd spotybot
pip install -e .[dev]
```

### Running Tests

```bash
pytest
```

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## ⚖️ Legal Notice

SpotyBot is a tool for educational and personal use. Please respect:
- 🎵 Artists' and creators' rights
- 📜 Spotify's Terms of Service
- 🌐 YouTube's Terms of Service
- 🏛️ Local copyright laws

Only download music you have the legal right to access.

## 🙏 Acknowledgments

- **[spotDL](https://github.com/spotDL/spotify-downloader)** - The amazing library that powers our downloads
- **[Spotipy](https://github.com/plamere/spotipy)** - Spotify Web API wrapper
- **[Rich](https://github.com/willmcgugan/rich)** - Beautiful terminal formatting
- **[Click](https://github.com/pallets/click)** - Command line interface framework

## 📊 Stats

- 🔥 **Built with Python 3.8+**
- ⚡ **Async/await support**
- 🎨 **Rich terminal UI**
- 🎵 **Multiple audio formats**
- 🔧 **Highly configurable**
- 🌍 **Cross-platform**

---

<div align="center">
  
**Made with ❤️ for music lovers**

[⬆️ Back to Top](#-spotybot---spotify-playlist-downloader)

</div>