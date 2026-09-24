"""
SpotyBot Modern GUI - Complete Refactor with CustomTkinter
A beautiful, modern interface for downloading Spotify content
"""

import os
import sys

# Disable locale/gettext before any other imports to prevent translation errors
os.environ['LC_ALL'] = 'C'
os.environ['LANG'] = 'C'
os.environ['LANGUAGE'] = 'C'
os.environ['LC_MESSAGES'] = 'C'

# Completely disable gettext to prevent translation file errors
import builtins
import gettext

# Create a no-op translation function
def null_translation(message):
    return message

# Override gettext functions globally
gettext.gettext = null_translation
gettext.ngettext = lambda singular, plural, n: singular if n == 1 else plural
gettext.translation = lambda *args, **kwargs: type('obj', (object,), {
    'gettext': lambda self, s: s,
    'ngettext': lambda self, s, p, n: s if n == 1 else p,
    'install': lambda self, *a, **kw: None,
    'ugettext': lambda self, s: s,
    'ungettext': lambda self, s, p, n: s if n == 1 else p,
})()

# Also install a dummy _ function globally
builtins._ = null_translation

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import threading
import logging

# Add common binary paths for macOS/Linux (for ffmpeg, etc.)
# This ensures GUI apps can find homebrew binaries
common_paths = [
    '/opt/homebrew/bin',      # ARM Mac (M1/M2/M3)
    '/usr/local/bin',         # Intel Mac / Linux
    '/usr/bin',               # Standard Linux
    '/bin'                    # Standard system
]
current_path = os.environ.get('PATH', '')
paths_to_add = [p for p in common_paths if p not in current_path and os.path.exists(p)]
if paths_to_add:
    os.environ['PATH'] = ':'.join(paths_to_add) + ':' + current_path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import customtkinter as ctk
    from tkinter import filedialog, messagebox
    from PIL import Image, ImageTk
except ImportError as e:
    print(f"Error: Required packages not installed. Run: pip install customtkinter pillow")
    sys.exit(1)

try:
    from spotybot import SpotyBot, Config
except ImportError:
    messagebox.showerror("Error", "SpotyBot modules not found. Please ensure the package is installed.")
    sys.exit(1)

# Set up logger
logger = logging.getLogger(__name__)

# CustomTkinter theme settings
ctk.set_appearance_mode("dark")  # "dark" or "light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"


class DownloadQueueItem:
    """Represents an item in the download queue"""
    def __init__(self, url: str, settings: Dict[str, Any]):
        self.url = url
        self.settings = settings
        self.status = "queued"  # queued, downloading, completed, failed
        self.progress = 0.0
        self.message = ""
        self.timestamp = datetime.now()
        self.tracks_completed = 0
        self.tracks_total = 0


class DownloadHistory:
    """Manages download history and statistics"""
    def __init__(self, history_file: Path):
        self.history_file = history_file
        self.history: List[Dict[str, Any]] = []
        self.load_history()
    
    def load_history(self):
        """Load history from JSON file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            except Exception as e:
                logger.error(f"Error loading history: {e}")
                self.history = []
    
    def save_history(self):
        """Save history to JSON file"""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump(self.history[-100:], f, indent=2)  # Keep last 100 entries
        except Exception as e:
            logger.error(f"Error saving history: {e}")
    
    def add_entry(self, url: str, status: str, tracks_count: int, settings: Dict[str, Any]):
        """Add entry to history"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "status": status,
            "tracks_count": tracks_count,
            "format": settings.get("format", "mp3"),
            "quality": settings.get("quality", "128k")
        }
        self.history.append(entry)
        self.save_history()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get download statistics"""
        total_downloads = len(self.history)
        successful = sum(1 for entry in self.history if entry['status'] == 'completed')
        total_tracks = sum(entry.get('tracks_count', 0) for entry in self.history)
        
        return {
            "total_downloads": total_downloads,
            "successful": successful,
            "failed": total_downloads - successful,
            "total_tracks": total_tracks
        }


class PresetManager:
    """Manages download presets"""
    def __init__(self, presets_file: Path):
        self.presets_file = presets_file
        self.presets: Dict[str, Dict[str, Any]] = {
            "High Quality": {"format": "flac", "quality": "320k", "metadata": True, "lyrics": True},
            "Standard": {"format": "mp3", "quality": "192k", "metadata": True, "lyrics": False},
            "Quick": {"format": "mp3", "quality": "128k", "metadata": False, "lyrics": False},
        }
        self.load_presets()
    
    def load_presets(self):
        """Load custom presets"""
        if self.presets_file.exists():
            try:
                with open(self.presets_file, 'r') as f:
                    custom_presets = json.load(f)
                    self.presets.update(custom_presets)
            except Exception as e:
                logger.error(f"Error loading presets: {e}")
    
    def save_preset(self, name: str, settings: Dict[str, Any]):
        """Save a new preset"""
        self.presets[name] = settings
        self._save_to_file()
    
    def delete_preset(self, name: str):
        """Delete a preset"""
        if name in self.presets:
            del self.presets[name]
            self._save_to_file()
    
    def _save_to_file(self):
        """Save presets to file"""
        try:
            self.presets_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.presets_file, 'w') as f:
                json.dump(self.presets, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving presets: {e}")


class ModernSpotyBotGUI(ctk.CTk):
    """Modern SpotyBot GUI with CustomTkinter"""
    
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("🎵 SpotyBot - Modern Spotify Downloader")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        
        # Initialize managers
        self.config_dir = self._get_config_dir()
        self.history_manager = DownloadHistory(self.config_dir / "history.json")
        self.preset_manager = PresetManager(self.config_dir / "presets.json")
        
        # State
        self.download_queue: List[DownloadQueueItem] = []
        self.current_download: Optional[DownloadQueueItem] = None
        self.bot: Optional[SpotyBot] = None
        self.is_downloading = False
        
        # Settings variables
        self.output_dir = ctk.StringVar(value=str(Path.home() / "Music" / "SpotyBot"))
        self.format_var = ctk.StringVar(value="mp3")
        self.quality_var = ctk.StringVar(value="192k")
        self.concurrent_var = ctk.IntVar(value=8)
        self.embed_metadata = ctk.BooleanVar(value=True)
        self.download_lyrics = ctk.BooleanVar(value=False)
        self.skip_existing = ctk.BooleanVar(value=True)
        self.max_tracks_var = ctk.StringVar(value="")
        self.theme_var = ctk.StringVar(value="dark")
        
        # Create UI
        self.create_sidebar()
        self.create_main_content()
        self.load_settings()
        
        # Start UI update loop
        self.update_ui_loop()
    
    def _get_config_dir(self) -> Path:
        """Get configuration directory"""
        if getattr(sys, 'frozen', False):
            config_dir = Path.home() / '.spotybot'
        else:
            config_dir = Path('.spotybot')
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    def create_sidebar(self):
        """Create modern sidebar navigation"""
        # Sidebar frame
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", rowspan=4)
        self.sidebar.grid_rowconfigure(10, weight=1)
        
        # Logo/Title
        logo_label = ctk.CTkLabel(
            self.sidebar,
            text="🎵 SpotyBot",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        version_label = ctk.CTkLabel(
            self.sidebar,
            text="v2.0 Modern",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        version_label.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("📥 Download", "download"),
            ("📋 Queue", "queue"),
            ("📊 History", "history"),
            ("⚙️ Settings", "settings"),
            ("ℹ️ About", "about")
        ]
        
        for idx, (text, page) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=lambda p=page: self.show_page(p),
                width=160,
                height=40,
                font=ctk.CTkFont(size=14),
                fg_color="transparent",
                hover_color=("gray70", "gray30")
            )
            btn.grid(row=idx, column=0, padx=20, pady=5)
            self.nav_buttons[page] = btn
        
        # Theme toggle
        theme_label = ctk.CTkLabel(self.sidebar, text="Theme:", font=ctk.CTkFont(size=12))
        theme_label.grid(row=20, column=0, padx=20, pady=(20, 5))
        
        self.theme_switch = ctk.CTkSegmentedButton(
            self.sidebar,
            values=["🌙 Dark", "☀️ Light"],
            command=self.change_theme,
            width=160
        )
        self.theme_switch.set("🌙 Dark")
        self.theme_switch.grid(row=21, column=0, padx=20, pady=5)
        
        # Statistics card
        self.stats_frame = ctk.CTkFrame(self.sidebar, corner_radius=10)
        self.stats_frame.grid(row=22, column=0, padx=20, pady=20, sticky="ew")
        
        stats_title = ctk.CTkLabel(
            self.stats_frame,
            text="📈 Statistics",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        stats_title.pack(pady=(10, 5))
        
        self.stats_text = ctk.CTkLabel(
            self.stats_frame,
            text="Loading...",
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        self.stats_text.pack(pady=(5, 10), padx=10)
        
        self.update_statistics_display()
    
    def create_main_content(self):
        """Create main content area with pages"""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Container for all pages
        self.pages = {}
        
        # Create pages
        self.pages["download"] = self.create_download_page()
        self.pages["queue"] = self.create_queue_page()
        self.pages["history"] = self.create_history_page()
        self.pages["settings"] = self.create_settings_page()
        self.pages["about"] = self.create_about_page()
        
        # Show default page
        self.show_page("download")
    
    def create_download_page(self) -> ctk.CTkFrame:
        """Create main download page"""
        page = ctk.CTkFrame(self, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)
        
        # Header
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        title = ctk.CTkLabel(
            header,
            text="Download Music",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            header,
            text="Enter Spotify URL or paste multiple URLs (one per line)",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle.pack(anchor="w")
        
        # URL Input Card
        url_card = ctk.CTkFrame(page, corner_radius=15)
        url_card.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        url_card.grid_columnconfigure(0, weight=1)
        
        url_label = ctk.CTkLabel(
            url_card,
            text="🔗 Spotify URL(s)",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        url_label.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))
        
        # URL Text Box (supports multiple URLs)
        self.url_textbox = ctk.CTkTextbox(
            url_card,
            height=120,
            font=ctk.CTkFont(size=13),
            corner_radius=10
        )
        self.url_textbox.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        
        # Quick presets
        preset_frame = ctk.CTkFrame(url_card, fg_color="transparent")
        preset_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        preset_label = ctk.CTkLabel(
            preset_frame,
            text="⚡ Quick Presets:",
            font=ctk.CTkFont(size=13)
        )
        preset_label.pack(side="left", padx=(0, 10))
        
        for preset_name in self.preset_manager.presets.keys():
            btn = ctk.CTkButton(
                preset_frame,
                text=preset_name,
                width=100,
                height=28,
                command=lambda p=preset_name: self.apply_preset(p),
                fg_color=("gray75", "gray25"),
                hover_color=("gray65", "gray35")
            )
            btn.pack(side="left", padx=5)
        
        # Action buttons
        button_frame = ctk.CTkFrame(url_card, fg_color="transparent")
        button_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 15))
        
        self.add_to_queue_btn = ctk.CTkButton(
            button_frame,
            text="📋 Add to Queue",
            command=self.add_to_queue,
            width=150,
            height=45,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40")
        )
        self.add_to_queue_btn.pack(side="left", padx=(0, 10))
        
        self.download_now_btn = ctk.CTkButton(
            button_frame,
            text="⚡ Download Now",
            command=self.download_now,
            width=150,
            height=45,
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.download_now_btn.pack(side="left", padx=(0, 10))
        
        self.clear_btn = ctk.CTkButton(
            button_frame,
            text="🗑️ Clear",
            command=lambda: self.url_textbox.delete("1.0", "end"),
            width=100,
            height=45,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90")
        )
        self.clear_btn.pack(side="left")
        
        # Current Download Status Card
        status_card = ctk.CTkFrame(page, corner_radius=15)
        status_card.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        status_card.grid_columnconfigure(0, weight=1)
        status_card.grid_rowconfigure(1, weight=1)
        
        status_title = ctk.CTkLabel(
            status_card,
            text="📊 Current Download",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        status_title.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 10))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(status_card, height=25, corner_radius=10)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        self.progress_bar.set(0)
        
        # Progress label
        self.progress_label = ctk.CTkLabel(
            status_card,
            text="Ready to download",
            font=ctk.CTkFont(size=14)
        )
        self.progress_label.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 5))
        
        # Status log
        self.status_textbox = ctk.CTkTextbox(
            status_card,
            height=200,
            font=ctk.CTkFont(family="Courier", size=11),
            corner_radius=10
        )
        self.status_textbox.grid(row=3, column=0, sticky="nsew", padx=20, pady=(10, 15))
        
        return page
    
    def create_queue_page(self) -> ctk.CTkFrame:
        """Create download queue page"""
        page = ctk.CTkFrame(self, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(page, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            header_frame,
            text="Download Queue",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w")
        
        # Queue controls
        controls = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls.grid(row=0, column=1, sticky="e")
        
        self.start_queue_btn = ctk.CTkButton(
            controls,
            text="▶️ Start Queue",
            command=self.start_queue,
            width=120,
            height=35
        )
        self.start_queue_btn.pack(side="left", padx=5)
        
        self.clear_queue_btn = ctk.CTkButton(
            controls,
            text="🗑️ Clear Queue",
            command=self.clear_queue,
            width=120,
            height=35,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90")
        )
        self.clear_queue_btn.pack(side="left", padx=5)
        
        # Queue list (scrollable)
        self.queue_frame = ctk.CTkScrollableFrame(page, corner_radius=15)
        self.queue_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.queue_frame.grid_columnconfigure(0, weight=1)
        
        return page
    
    def create_history_page(self) -> ctk.CTkFrame:
        """Create download history page"""
        page = ctk.CTkFrame(self, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        title = ctk.CTkLabel(
            header,
            text="Download History",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.pack(side="left")
        
        clear_history_btn = ctk.CTkButton(
            header,
            text="🗑️ Clear History",
            command=self.clear_history,
            width=120,
            height=35,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90")
        )
        clear_history_btn.pack(side="right")
        
        # History list
        self.history_frame = ctk.CTkScrollableFrame(page, corner_radius=15)
        self.history_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.history_frame.grid_columnconfigure(0, weight=1)
        
        self.update_history_display()
        
        return page
    
    def create_settings_page(self) -> ctk.CTkFrame:
        """Create settings page"""
        page = ctk.CTkScrollableFrame(self, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        
        # Header
        title = ctk.CTkLabel(
            page,
            text="Settings",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))
        
        # Output Directory Section
        output_section = ctk.CTkFrame(page, corner_radius=15)
        output_section.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        output_section.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            output_section,
            text="📁 Download Location",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(15, 10))
        
        ctk.CTkEntry(
            output_section,
            textvariable=self.output_dir,
            height=40,
            font=ctk.CTkFont(size=13)
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=(20, 10), pady=(0, 15))
        
        ctk.CTkButton(
            output_section,
            text="Browse",
            command=self.browse_folder,
            width=100,
            height=40
        ).grid(row=1, column=2, padx=(0, 20), pady=(0, 15))
        
        # Audio Settings Section
        audio_section = ctk.CTkFrame(page, corner_radius=15)
        audio_section.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        audio_section.grid_columnconfigure(1, weight=1)
        audio_section.grid_columnconfigure(3, weight=1)
        
        ctk.CTkLabel(
            audio_section,
            text="🎵 Audio Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=20, pady=(15, 10))
        
        # Format
        ctk.CTkLabel(audio_section, text="Format:", font=ctk.CTkFont(size=14)).grid(
            row=1, column=0, sticky="w", padx=(20, 10), pady=10
        )
        ctk.CTkOptionMenu(
            audio_section,
            variable=self.format_var,
            values=["mp3", "flac", "ogg", "opus", "m4a"],
            width=150,
            height=35
        ).grid(row=1, column=1, sticky="w", padx=(0, 20), pady=10)
        
        # Quality
        ctk.CTkLabel(audio_section, text="Quality:", font=ctk.CTkFont(size=14)).grid(
            row=1, column=2, sticky="w", padx=(20, 10), pady=10
        )
        ctk.CTkOptionMenu(
            audio_section,
            variable=self.quality_var,
            values=["96k", "128k", "160k", "192k", "256k", "320k"],
            width=150,
            height=35
        ).grid(row=1, column=3, sticky="w", padx=(0, 20), pady=10)
        
        # Concurrent downloads
        ctk.CTkLabel(audio_section, text="Concurrent Downloads:", font=ctk.CTkFont(size=14)).grid(
            row=2, column=0, sticky="w", padx=(20, 10), pady=(0, 15)
        )
        ctk.CTkSlider(
            audio_section,
            from_=1,
            to=12,
            number_of_steps=11,
            variable=self.concurrent_var,
            width=200
        ).grid(row=2, column=1, sticky="w", padx=(0, 10), pady=(0, 15))
        
        self.concurrent_label = ctk.CTkLabel(
            audio_section,
            text=f"{self.concurrent_var.get()}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.concurrent_label.grid(row=2, column=2, sticky="w", padx=(0, 20), pady=(0, 15))
        self.concurrent_var.trace_add('write', self.update_concurrent_label)
        
        # Options Section
        options_section = ctk.CTkFrame(page, corner_radius=15)
        options_section.grid(row=3, column=0, sticky="ew", padx=20, pady=10)
        
        ctk.CTkLabel(
            options_section,
            text="⚙️ Download Options",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))
        
        ctk.CTkCheckBox(
            options_section,
            text="Embed Metadata & Album Art",
            variable=self.embed_metadata,
            font=ctk.CTkFont(size=14)
        ).grid(row=1, column=0, sticky="w", padx=20, pady=5)
        
        ctk.CTkCheckBox(
            options_section,
            text="Download Lyrics (.lrc files)",
            variable=self.download_lyrics,
            font=ctk.CTkFont(size=14)
        ).grid(row=2, column=0, sticky="w", padx=20, pady=5)
        
        ctk.CTkCheckBox(
            options_section,
            text="Skip Existing Files",
            variable=self.skip_existing,
            font=ctk.CTkFont(size=14)
        ).grid(row=3, column=0, sticky="w", padx=20, pady=(5, 15))
        
        # Max Tracks Section
        limit_section = ctk.CTkFrame(page, corner_radius=15)
        limit_section.grid(row=4, column=0, sticky="ew", padx=20, pady=10)
        limit_section.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            limit_section,
            text="🔢 Download Limits",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(
            limit_section,
            text="Max Tracks per Playlist (leave empty for no limit):",
            font=ctk.CTkFont(size=14)
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 15))
        
        ctk.CTkEntry(
            limit_section,
            textvariable=self.max_tracks_var,
            placeholder_text="No limit",
            width=150,
            height=35
        ).grid(row=1, column=1, sticky="e", padx=20, pady=(0, 15))
        
        # Save button
        save_btn = ctk.CTkButton(
            page,
            text="💾 Save Settings",
            command=self.save_settings,
            width=200,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        save_btn.grid(row=5, column=0, padx=20, pady=20)
        
        return page
    
    def create_about_page(self) -> ctk.CTkFrame:
        """Create about page"""
        page = ctk.CTkFrame(self, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)
        
        # Center content
        content = ctk.CTkFrame(page, corner_radius=20)
        content.grid(row=0, column=0, padx=100, pady=100, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        
        # Logo
        logo = ctk.CTkLabel(
            content,
            text="🎵",
            font=ctk.CTkFont(size=80)
        )
        logo.pack(pady=(40, 10))
        
        # Title
        title = ctk.CTkLabel(
            content,
            text="SpotyBot Modern",
            font=ctk.CTkFont(size=36, weight="bold")
        )
        title.pack(pady=10)
        
        # Version
        version = ctk.CTkLabel(
            content,
            text="Version 2.0.0",
            font=ctk.CTkFont(size=18),
            text_color="gray"
        )
        version.pack(pady=5)
        
        # Description
        desc = ctk.CTkLabel(
            content,
            text="A modern, beautiful Spotify downloader\nbuilt with CustomTkinter",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        desc.pack(pady=20)
        
        # Features
        features_frame = ctk.CTkFrame(content, fg_color="transparent")
        features_frame.pack(pady=20)
        
        features = [
            "✨ Modern dark/light theme",
            "📋 Download queue system",
            "📊 Download history & statistics",
            "⚡ Batch URL processing",
            "🎵 Multiple format support",
            "🎨 Beautiful, intuitive interface"
        ]
        
        for feature in features:
            ctk.CTkLabel(
                features_frame,
                text=feature,
                font=ctk.CTkFont(size=14)
            ).pack(anchor="w", pady=3)
        
        # Footer
        footer = ctk.CTkLabel(
            content,
            text="Powered by spotDL and CustomTkinter\n© 2026 SpotyBot",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        footer.pack(pady=(30, 40))
        
        return page
    
    def show_page(self, page_name: str):
        """Show specific page"""
        # Hide all pages
        for page in self.pages.values():
            page.grid_forget()
        
        # Show selected page
        if page_name in self.pages:
            self.pages[page_name].grid(row=0, column=1, sticky="nsew")
            
            # Update navigation button colors
            for name, btn in self.nav_buttons.items():
                if name == page_name:
                    btn.configure(fg_color=("gray75", "gray28"))
                else:
                    btn.configure(fg_color="transparent")
    
    def change_theme(self, value: str):
        """Change app theme"""
        if "Dark" in value:
            ctk.set_appearance_mode("dark")
            self.theme_var.set("dark")
        else:
            ctk.set_appearance_mode("light")
            self.theme_var.set("light")
    
    def apply_preset(self, preset_name: str):
        """Apply a preset configuration"""
        if preset_name in self.preset_manager.presets:
            preset = self.preset_manager.presets[preset_name]
            self.format_var.set(preset.get("format", "mp3"))
            self.quality_var.set(preset.get("quality", "192k"))
            self.embed_metadata.set(preset.get("metadata", True))
            self.download_lyrics.set(preset.get("lyrics", False))
            self.log_status(f"✨ Applied preset: {preset_name}")
    
    def browse_folder(self):
        """Browse for output folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.output_dir.set(folder)
    
    def add_to_queue(self):
        """Add URLs from textbox to download queue"""
        urls_text = self.url_textbox.get("1.0", "end").strip()
        if not urls_text:
            messagebox.showwarning("Warning", "Please enter at least one URL")
            return
        
        # Split by newlines to get multiple URLs
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        
        settings = self.get_current_settings()
        
        for url in urls:
            item = DownloadQueueItem(url, settings)
            self.download_queue.append(item)
        
        self.log_status(f"📋 Added {len(urls)} item(s) to queue")
        self.url_textbox.delete("1.0", "end")
        self.update_queue_display()
        
        # Auto-switch to queue page
        self.show_page("queue")
    
    def download_now(self):
        """Download current URL immediately"""
        urls_text = self.url_textbox.get("1.0", "end").strip()
        if not urls_text:
            messagebox.showwarning("Warning", "Please enter a URL")
            return
        
        # Take first URL
        url = urls_text.split('\n')[0].strip()
        
        if self.is_downloading:
            messagebox.showwarning("Warning", "Download already in progress!")
            return
        
        settings = self.get_current_settings()
        item = DownloadQueueItem(url, settings)
        
        # Add to front of queue and start
        self.download_queue.insert(0, item)
        self.start_queue()
    
    def start_queue(self):
        """Start processing download queue"""
        if self.is_downloading:
            self.log_status("⚠️ Download already in progress")
            return
        
        if not self.download_queue:
            self.log_status("📋 Queue is empty")
            return
        
        self.is_downloading = True
        self.log_status("🚀 Starting download queue...")
        
        # Start download thread
        thread = threading.Thread(target=self.process_queue, daemon=True)
        thread.start()
    
    def process_queue(self):
        """Process all items in download queue"""
        processed_count = 0
        
        while self.download_queue:
            item = self.download_queue[0]
            self.current_download = item
            item.status = "downloading"
            processed_count += 1
            
            try:
                self.download_item(item)
                item.status = "completed"
                self.log_status(f"✅ Completed: {item.url[:50]}...")
                
                # Add to history
                self.history_manager.add_entry(
                    item.url,
                    "completed",
                    item.tracks_completed,
                    item.settings
                )
                
            except Exception as e:
                item.status = "failed"
                item.message = str(e)
                self.log_status(f"❌ Failed: {str(e)}")
                
                # Add to history
                self.history_manager.add_entry(
                    item.url,
                    "failed",
                    0,
                    item.settings
                )
            
            # Remove from queue
            self.download_queue.pop(0)
            self.current_download = None
            
            # Update displays on main thread (thread-safe)
            self.after(0, self.update_queue_display)
            self.after(0, self.update_history_display)
            self.after(0, self.update_statistics_display)
        
        self.is_downloading = False
        
        # Only show completion notification if we processed at least one item
        if processed_count > 0:
            self.log_status("🎉 Queue completed!")
            self.show_completion_notification()
        else:
            self.log_status("📋 Queue was empty")
    
    def download_item(self, item: DownloadQueueItem):
        """Download a single queue item with retry logic"""
        max_retries = 2
        retry_count = 0
        last_error = None
        
        while retry_count <= max_retries:
            try:
                # Initialize bot if needed
                if self.bot is None:
                    config = self.create_config(item.settings)
                    self.bot = SpotyBot(config)
                    self.log_status("✅ SpotyBot initialized")
                
                url = item.url
                self.log_status(f"🎵 Processing: {url}")
                
                # Auto-detect URL type
                url_type, is_valid = self.bot.validate_url(url)
                
                if not is_valid:
                    raise Exception("Invalid Spotify URL")
                
                self.log_status(f"🎯 Detected: {url_type}")
                
                # Download based on type
                if url_type == "playlist":
                    max_tracks = int(item.settings.get("max_tracks")) if item.settings.get("max_tracks") else None
                    playlist_info, results = self.bot.downloader.download_playlist(url, max_tracks=max_tracks, use_async=False)
                    item.tracks_completed = sum(1 for r in results if r.success)
                    item.tracks_total = len(results)
                    self.log_status(f"📊 Downloaded {item.tracks_completed}/{item.tracks_total} tracks")
                    
                elif url_type == "album":
                    results = self.bot.download_album(url, use_async=False, show_summary=False)
                    item.tracks_completed = sum(1 for r in results if r.success)
                    item.tracks_total = len(results)
                    self.log_status(f"💿 Downloaded {item.tracks_completed}/{item.tracks_total} tracks from album")
                    
                elif url_type == "track":
                    success = self.bot.download_track(url, show_summary=False)
                    item.tracks_completed = 1 if success else 0
                    item.tracks_total = 1
                    self.log_status("🎤 Track downloaded successfully")
                
                item.progress = 100.0
                # Success - break out of retry loop
                break
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Check if it's a retryable error
                is_retryable = any(keyword in error_str for keyword in [
                    'decompressing', 'header check', 'connection', 'timeout', 
                    'network', 'temporary', 'timed out', 'reset'
                ])
                
                if is_retryable and retry_count < max_retries:
                    retry_count += 1
                    self.log_status(f"⚠️  Download error (attempt {retry_count}/{max_retries + 1}). Retrying...")
                    
                    # Reinitialize bot on network/connection errors
                    if 'connection' in error_str or 'network' in error_str:
                        self.bot = None
                    
                    # Brief delay before retry
                    import time
                    time.sleep(2)
                else:
                    # Non-retryable error or max retries reached
                    error_msg = str(last_error)
                    # Simplify common error messages
                    if 'decompressing' in error_str:
                        error_msg = "Download corrupted. The audio source may be temporarily unavailable."
                    elif 'connection' in error_str or 'network' in error_str:
                        error_msg = "Network connection issue. Please check your internet connection."
                    
                    raise Exception(error_msg)
        
        # If we exhausted retries, raise the last error
        if retry_count > max_retries and last_error:
            raise last_error
    
    def clear_queue(self):
        """Clear download queue"""
        if messagebox.askyesno("Confirm", "Clear all items from queue?"):
            self.download_queue.clear()
            self.update_queue_display()
            self.log_status("🗑️ Queue cleared")
    
    def update_queue_display(self):
        """Update queue page display"""
        # Clear existing widgets
        for widget in self.queue_frame.winfo_children():
            widget.destroy()
        
        if not self.download_queue:
            empty_label = ctk.CTkLabel(
                self.queue_frame,
                text="📭 Queue is empty\n\nAdd URLs from the Download page",
                font=ctk.CTkFont(size=16),
                text_color="gray"
            )
            empty_label.pack(pady=100)
            return
        
        # Display queue items
        for idx, item in enumerate(self.download_queue):
            self.create_queue_item_widget(item, idx)
    
    def create_queue_item_widget(self, item: DownloadQueueItem, index: int):
        """Create widget for queue item"""
        item_frame = ctk.CTkFrame(self.queue_frame, corner_radius=10)
        item_frame.grid(row=index, column=0, sticky="ew", padx=10, pady=5)
        item_frame.grid_columnconfigure(1, weight=1)
        
        # Status indicator
        status_colors = {
            "queued": "gray",
            "downloading": "blue",
            "completed": "green",
            "failed": "red"
        }
        status_emoji = {
            "queued": "⏳",
            "downloading": "⬇️",
            "completed": "✅",
            "failed": "❌"
        }
        
        status_label = ctk.CTkLabel(
            item_frame,
            text=status_emoji.get(item.status, "⏳"),
            font=ctk.CTkFont(size=20),
            width=40
        )
        status_label.grid(row=0, column=0, padx=15, pady=15)
        
        # URL and info
        info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew", pady=15)
        
        url_text = item.url if len(item.url) <= 70 else item.url[:67] + "..."
        url_label = ctk.CTkLabel(
            info_frame,
            text=url_text,
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        url_label.pack(anchor="w")
        
        details_text = f"{item.settings['format']} | {item.settings['quality']}"
        if item.tracks_total > 0:
            details_text += f" | {item.tracks_completed}/{item.tracks_total} tracks"
        
        details_label = ctk.CTkLabel(
            info_frame,
            text=details_text,
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        details_label.pack(anchor="w")
        
        # Remove button
        if item.status == "queued":
            remove_btn = ctk.CTkButton(
                item_frame,
                text="🗑️",
                width=40,
                height=40,
                command=lambda: self.remove_from_queue(index),
                fg_color="transparent",
                hover_color=("gray70", "gray30")
            )
            remove_btn.grid(row=0, column=2, padx=15)
    
    def remove_from_queue(self, index: int):
        """Remove item from queue"""
        if 0 <= index < len(self.download_queue):
            self.download_queue.pop(index)
            self.update_queue_display()
    
    def update_history_display(self):
        """Update history page display"""
        # Clear existing widgets
        for widget in self.history_frame.winfo_children():
            widget.destroy()
        
        history = list(reversed(self.history_manager.history))  # Show newest first
        
        if not history:
            empty_label = ctk.CTkLabel(
                self.history_frame,
                text="📜 No download history yet\n\nStart downloading to build your history",
                font=ctk.CTkFont(size=16),
                text_color="gray"
            )
            empty_label.pack(pady=100)
            return
        
        # Display history items (limit to last 50)
        for idx, entry in enumerate(history[:50]):
            self.create_history_item_widget(entry, idx)
    
    def create_history_item_widget(self, entry: Dict[str, Any], index: int):
        """Create widget for history item"""
        item_frame = ctk.CTkFrame(self.history_frame, corner_radius=10)
        item_frame.grid(row=index, column=0, sticky="ew", padx=10, pady=5)
        item_frame.grid_columnconfigure(1, weight=1)
        
        # Status
        status_emoji = "✅" if entry['status'] == 'completed' else "❌"
        status_label = ctk.CTkLabel(
            item_frame,
            text=status_emoji,
            font=ctk.CTkFont(size=20),
            width=40
        )
        status_label.grid(row=0, column=0, padx=15, pady=15)
        
        # Info
        info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew", pady=15)
        
        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(entry['timestamp'])
            time_str = timestamp.strftime("%Y-%m-%d %H:%M")
        except:
            time_str = "Unknown time"
        
        url_text = entry['url'] if len(entry['url']) <= 60 else entry['url'][:57] + "..."
        url_label = ctk.CTkLabel(
            info_frame,
            text=url_text,
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        url_label.pack(anchor="w")
        
        details = f"{time_str} | {entry.get('tracks_count', 0)} tracks | {entry.get('format', 'mp3')} {entry.get('quality', '192k')}"
        details_label = ctk.CTkLabel(
            info_frame,
            text=details,
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        details_label.pack(anchor="w")
    
    def clear_history(self):
        """Clear download history"""
        if messagebox.askyesno("Confirm", "Clear all download history?"):
            self.history_manager.history.clear()
            self.history_manager.save_history()
            self.update_history_display()
            self.update_statistics_display()
            self.log_status("🗑️ History cleared")
    
    def update_statistics_display(self):
        """Update statistics in sidebar"""
        stats = self.history_manager.get_statistics()
        stats_text = f"""Total: {stats['total_downloads']}
Success: {stats['successful']}
Failed: {stats['failed']}
Tracks: {stats['total_tracks']}"""
        self.stats_text.configure(text=stats_text)
    
    def update_concurrent_label(self, *args):
        """Update concurrent downloads label"""
        self.concurrent_label.configure(text=f"{self.concurrent_var.get()}")
    
    def get_current_settings(self) -> Dict[str, Any]:
        """Get current settings as dictionary"""
        return {
            "format": self.format_var.get(),
            "quality": self.quality_var.get(),
            "output_dir": self.output_dir.get(),
            "concurrent": self.concurrent_var.get(),
            "metadata": self.embed_metadata.get(),
            "lyrics": self.download_lyrics.get(),
            "skip_existing": self.skip_existing.get(),
            "max_tracks": self.max_tracks_var.get()
        }
    
    def create_config(self, settings: Dict[str, Any]) -> Config:
        """Create Config object from settings"""
        output_path = Path(settings["output_dir"])
        output_path.mkdir(parents=True, exist_ok=True)
        
        return Config(
            spotify_client_id="5a8524a2e621475d8cb57ef4900e4edb",
            spotify_client_secret="6117d497466e42e494e377aa8b1f8312",
            download_format=settings["format"],
            download_quality=settings["quality"],
            output_directory=output_path,
            max_concurrent_downloads=settings["concurrent"],
            embed_metadata=settings["metadata"],
            download_lyrics=settings["lyrics"],
            skip_existing_files=settings["skip_existing"],
            show_progress=False,
            log_level="INFO"
        )
    
    def load_settings(self):
        """Load settings from file"""
        settings_file = self.config_dir / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    self.output_dir.set(settings.get("output_dir", str(Path.home() / "Music" / "SpotyBot")))
                    self.format_var.set(settings.get("format", "mp3"))
                    self.quality_var.set(settings.get("quality", "192k"))
                    self.concurrent_var.set(settings.get("concurrent", 8))
                    self.embed_metadata.set(settings.get("metadata", True))
                    self.download_lyrics.set(settings.get("lyrics", False))
                    self.skip_existing.set(settings.get("skip_existing", True))
                    self.max_tracks_var.set(settings.get("max_tracks", ""))
                    self.theme_var.set(settings.get("theme", "dark"))
                    
                    # Apply theme
                    theme_value = "🌙 Dark" if self.theme_var.get() == "dark" else "☀️ Light"
                    self.theme_switch.set(theme_value)
                    ctk.set_appearance_mode(self.theme_var.get())
                    
                    self.log_status("✅ Settings loaded")
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to file"""
        settings = self.get_current_settings()
        settings["theme"] = self.theme_var.get()
        
        settings_file = self.config_dir / "settings.json"
        try:
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            self.log_status("💾 Settings saved successfully")
            messagebox.showinfo("Success", "Settings saved successfully!")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Could not save settings: {e}")
    
    def log_status(self, message: str):
        """Log message to status textbox (thread-safe)"""
        def _log():
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.status_textbox.insert("end", f"[{timestamp}] {message}\n")
            self.status_textbox.see("end")
        
        # Schedule on main thread if called from background thread
        self.after(0, _log)
    
    def show_completion_notification(self):
        """Show completion notification"""
        self.after(0, lambda: messagebox.showinfo(
            "Download Complete",
            "All downloads in queue have been completed!"
        ))
    
    def update_ui_loop(self):
        """Update UI periodically"""
        # Update progress bar if downloading
        if self.current_download:
            self.progress_bar.set(self.current_download.progress / 100.0)
            self.progress_label.configure(
                text=f"Downloading: {self.current_download.url[:50]}..."
            )
        else:
            if self.is_downloading:
                self.progress_label.configure(text="Processing queue...")
            else:
                self.progress_bar.set(0)
                self.progress_label.configure(text="Ready to download")
        
        # Schedule next update
        self.after(500, self.update_ui_loop)


def main():
    """Main function to run the modern GUI"""
    try:
        app = ModernSpotyBotGUI()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Could not start SpotyBot: {e}")
        logger.exception("Fatal error:")


if __name__ == "__main__":
    main()
