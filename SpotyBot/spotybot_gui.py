"""
SpotyBot Simple GUI Interface
A user-friendly interface for downloading Spotify playlists, albums, and tracks
"""

import os
import sys

# Disable locale/gettext before any other imports to prevent translation errors
os.environ['LC_ALL'] = 'C'
os.environ['LANG'] = 'C'
os.environ['LANGUAGE'] = 'C'
os.environ['LC_MESSAGES'] = 'C'

# Disable gettext to prevent translation file errors
import builtins
_original_gettext = None
try:
    import gettext as _gettext_module
    _original_gettext = _gettext_module.gettext
    # Override gettext to return the message as-is (no translation)
    _gettext_module.gettext = lambda message: message
    _gettext_module.ngettext = lambda singular, plural, n: singular if n == 1 else plural
    _gettext_module.translation = lambda *args, **kwargs: type('obj', (object,), {
        'gettext': lambda self, s: s,
        'ngettext': lambda self, s, p, n: s if n == 1 else p,
        'install': lambda self, *a, **kw: None
    })()
except:
    pass

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path
import locale

# Set locale to avoid translation file errors
try:
    locale.setlocale(locale.LC_ALL, 'C')
except:
    pass

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Add bundled ffmpeg to PATH when running from PyInstaller bundle
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    bundle_dir = sys._MEIPASS
    # Check for ffmpeg in common bundle locations
    possible_ffmpeg_paths = [
        os.path.join(bundle_dir, 'ffmpeg'),
        os.path.join(os.path.dirname(sys.executable), 'ffmpeg'),
        os.path.join(os.path.dirname(os.path.dirname(sys.executable)), 'Frameworks', 'ffmpeg'),
    ]
    for ffmpeg_path in possible_ffmpeg_paths:
        if os.path.exists(ffmpeg_path):
            ffmpeg_dir = os.path.dirname(ffmpeg_path)
            os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
            break
    
    # Disable locale to avoid gettext translation errors in bundle
    os.environ['LC_ALL'] = 'C'
    os.environ['LANG'] = 'C'

try:
    from spotybot import SpotyBot, Config
except ImportError:
    messagebox.showerror("Error", "SpotyBot modules not found. Please ensure the package is installed.")
    sys.exit(1)


class SpotyBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎵 SpotyBot - Spotify Downloader")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Variables
        self.url_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value="./downloads")
        self.format_var = tk.StringVar(value="mp3")
        self.quality_var = tk.StringVar(value="128k")
        self.concurrent_var = tk.StringVar(value="8")
        self.embed_metadata_var = tk.BooleanVar(value=False)
        self.download_lyrics_var = tk.BooleanVar(value=False)
        self.skip_existing_var = tk.BooleanVar(value=True)
        self.max_tracks_var = tk.StringVar(value="")
        
        self.downloading = False
        self.bot = None
        
        self.create_widgets()
        self.load_settings()
    
    def get_config_file_path(self):
        """Get the path to the config file - use writable location for bundled app"""
        if getattr(sys, 'frozen', False):
            # Running as bundled app - use user's home directory
            config_dir = Path.home() / '.spotybot'
            config_dir.mkdir(parents=True, exist_ok=True)
            return config_dir / '.env'
        else:
            # Running from source - use current directory
            return Path('.env')
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎵 SpotyBot", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # URL Input Section
        ttk.Label(main_frame, text="Spotify URL:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        url_frame = ttk.Frame(main_frame)
        url_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(0, weight=1)
        
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=("Arial", 10))
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Auto-detect label
        detect_label = ttk.Label(main_frame, text="✨ Auto-detects: Playlists, Albums, Tracks | 📁 Creates subfolders for collections", 
                                font=("Arial", 9), foreground="gray")
        detect_label.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(0, 15))
        
        # Output Directory Section
        ttk.Label(main_frame, text="Download Folder:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=tk.W, pady=5)
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        dir_frame.columnconfigure(0, weight=1)
        
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.output_dir_var, font=("Arial", 10))
        self.dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(dir_frame, text="Browse", command=self.browse_folder).grid(row=0, column=1)
        
        # Settings Section
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ Settings", padding="10")
        settings_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        settings_frame.columnconfigure(1, weight=1)
        
        # Quality and Format
        ttk.Label(settings_frame, text="Quality:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        quality_combo = ttk.Combobox(settings_frame, textvariable=self.quality_var, 
                                   values=["96k", "128k", "160k", "192k", "256k", "320k"],
                                   state="readonly", width=10)
        quality_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(settings_frame, text="Format:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        format_combo = ttk.Combobox(settings_frame, textvariable=self.format_var,
                                  values=["mp3", "flac", "ogg", "opus", "m4a"],
                                  state="readonly", width=10)
        format_combo.grid(row=0, column=3, sticky=tk.W)
        
        # Concurrent Downloads
        ttk.Label(settings_frame, text="Concurrent Downloads:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        concurrent_combo = ttk.Combobox(settings_frame, textvariable=self.concurrent_var,
                                      values=["1", "2", "4", "6", "8", "10", "12"],
                                      state="readonly", width=10)
        concurrent_combo.grid(row=1, column=1, sticky=tk.W, pady=(10, 0), padx=(0, 20))
        
        # Max Tracks
        ttk.Label(settings_frame, text="Max Tracks (optional):").grid(row=1, column=2, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        max_tracks_entry = ttk.Entry(settings_frame, textvariable=self.max_tracks_var, width=10)
        max_tracks_entry.grid(row=1, column=3, sticky=tk.W, pady=(10, 0))
        
        # Checkboxes
        ttk.Checkbutton(settings_frame, text="Embed Metadata", 
                       variable=self.embed_metadata_var).grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        ttk.Checkbutton(settings_frame, text="Download Lyrics", 
                       variable=self.download_lyrics_var).grid(row=2, column=1, sticky=tk.W, pady=(10, 0))
        ttk.Checkbutton(settings_frame, text="Skip Existing Files", 
                       variable=self.skip_existing_var).grid(row=2, column=2, sticky=tk.W, pady=(10, 0))
        
        # Buttons Section
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=(0, 15))
        
        self.download_btn = ttk.Button(button_frame, text="🎵 Download", 
                                     command=self.start_download, style="Accent.TButton")
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="💾 Save Settings", command=self.save_settings).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="🔄 Reset to Default", command=self.reset_settings).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="ℹ️ Help", command=self.show_help).pack(side=tk.LEFT)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="📊 Progress", padding="10")
        progress_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(1, weight=1)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status text area
        self.status_text = scrolledtext.ScrolledText(progress_frame, height=12, wrap=tk.WORD,
                                                   font=("Consolas", 9))
        self.status_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure main frame grid weights
        main_frame.rowconfigure(8, weight=1)
    
    def browse_folder(self):
        """Open folder selection dialog"""
        folder = filedialog.askdirectory()
        if folder:
            self.output_dir_var.set(folder)
    
    def load_settings(self):
        """Load settings from .env file"""
        try:
            config_path = self.get_config_file_path()
            config = Config.from_env(str(config_path) if config_path.exists() else None)
            self.output_dir_var.set(str(config.output_directory))
            self.format_var.set(config.download_format)
            self.quality_var.set(config.download_quality)
            self.concurrent_var.set(str(config.max_concurrent_downloads))
            self.embed_metadata_var.set(config.embed_metadata)
            self.download_lyrics_var.set(config.download_lyrics)
            self.skip_existing_var.set(config.skip_existing_files)
            self.log(f"✅ Settings loaded from {config_path}")
        except Exception as e:
            self.log(f"⚠️ Could not load settings: {e}")
    
    def save_settings(self):
        """Save current settings to .env file"""
        try:
            config_path = self.get_config_file_path()
            config_content = f"""# Spotify API Configuration
SPOTIFY_CLIENT_ID=5a8524a2e621475d8cb57ef4900e4edb
SPOTIFY_CLIENT_SECRET=6117d497466e42e494e377aa8b1f8312

# Download Configuration
DOWNLOAD_FORMAT={self.format_var.get()}
DOWNLOAD_QUALITY={self.quality_var.get()}
OUTPUT_DIRECTORY={self.output_dir_var.get()}

# Download Behavior
MAX_CONCURRENT_DOWNLOADS={self.concurrent_var.get()}
SKIP_EXISTING_FILES={str(self.skip_existing_var.get()).lower()}
EMBED_METADATA={str(self.embed_metadata_var.get()).lower()}
DOWNLOAD_LYRICS={str(self.download_lyrics_var.get()).lower()}

# Audio Provider
AUDIO_PROVIDER=youtube-music
"""
            
            with open(config_path, "w") as f:
                f.write(config_content)
            
            # Reset bot instance to apply new settings on next download
            self.bot = None
            
            self.log(f"💾 Settings saved to {config_path}")
            messagebox.showinfo("Success", "Settings saved successfully!")
            
        except Exception as e:
            self.log(f"❌ Error saving settings: {e}")
            messagebox.showerror("Error", f"Could not save settings: {e}")
    
    def reset_settings(self):
        """Reset to default settings"""
        self.output_dir_var.set("./downloads")
        self.format_var.set("mp3")
        self.quality_var.set("128k")
        self.concurrent_var.set("8")
        self.embed_metadata_var.set(False)
        self.download_lyrics_var.set(False)
        self.skip_existing_var.set(True)
        self.max_tracks_var.set("")
        self.log("🔄 Settings reset to default values")
    
    def log(self, message):
        """Add message to status text area"""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.root.update()
    
    def validate_inputs(self):
        """Validate user inputs"""
        if not self.url_var.get().strip():
            messagebox.showerror("Error", "Please enter a Spotify URL")
            return False
        
        if not self.output_dir_var.get().strip():
            messagebox.showerror("Error", "Please select an output directory")
            return False
        
        # Check if URL looks like Spotify URL
        url = self.url_var.get().strip()
        if "spotify.com" not in url:
            result = messagebox.askyesno("Warning", 
                                       "This doesn't look like a Spotify URL. Continue anyway?")
            if not result:
                return False
        
        return True
    
    def create_config(self):
        """Create Config object from GUI settings"""
        # Create output directory if it doesn't exist
        output_path = Path(self.output_dir_var.get())
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create config
        config = Config(
            spotify_client_id="5a8524a2e621475d8cb57ef4900e4edb",
            spotify_client_secret="6117d497466e42e494e377aa8b1f8312",
            download_format=self.format_var.get(),
            download_quality=self.quality_var.get(),
            output_directory=output_path,
            max_concurrent_downloads=int(self.concurrent_var.get()),
            embed_metadata=self.embed_metadata_var.get(),
            download_lyrics=self.download_lyrics_var.get(),
            skip_existing_files=self.skip_existing_var.get(),
            show_progress=False,  # We handle progress in GUI
            log_level="INFO"
        )
        
        return config
    
    def start_download(self):
        """Start download in separate thread"""
        if not self.validate_inputs():
            return
        
        if self.downloading:
            messagebox.showwarning("Warning", "Download already in progress!")
            return
        
        # Start download thread
        self.downloading = True
        self.download_btn.config(text="⏳ Downloading...", state="disabled")
        self.progress_var.set(0)
        self.status_text.delete(1.0, tk.END)
        
        thread = threading.Thread(target=self.download_thread, daemon=True)
        thread.start()
    
    def download_thread(self):
        """Download thread function"""
        try:
            self.log("🔧 Initializing SpotyBot...")
            
            # Create config
            config = self.create_config()
            
            # Reuse existing bot if available, otherwise create new one
            if self.bot is None:
                self.bot = SpotyBot(config)
                self.log("✅ SpotyBot initialized successfully")
            else:
                # Update config for existing bot
                self.bot.config = config
                self.bot.downloader.config = config
                self.log("✅ Using existing SpotyBot instance")
            
            url = self.url_var.get().strip()
            self.log(f"🎵 Processing URL: {url}")
            
            # Auto-detect URL type
            url_type, is_valid = self.bot.validate_url(url)
            
            if not is_valid:
                self.log("⚠️ Not a recognized Spotify URL, treating as search query...")
                self.download_search(url)
            else:
                self.log(f"🎯 Detected: {url_type}")
                
                # Get max tracks limit
                max_tracks = None
                if self.max_tracks_var.get().strip():
                    try:
                        max_tracks = int(self.max_tracks_var.get().strip())
                    except ValueError:
                        self.log("⚠️ Invalid max tracks value, ignoring...")
                
                # Download based on type
                if url_type == "playlist":
                    self.download_playlist(url, max_tracks)
                elif url_type == "album":
                    self.download_album(url)
                elif url_type == "track":
                    self.download_track(url)
            
        except Exception as e:
            self.log(f"❌ Error: {e}")
            messagebox.showerror("Error", f"Download failed: {e}")
        
        finally:
            self.downloading = False
            self.root.after(0, lambda: self.download_btn.config(text="🎵 Download", state="normal"))
    
    def download_playlist(self, url, max_tracks=None):
        """Download playlist with progress tracking"""
        try:
            # Get playlist info
            info = self.bot.get_playlist_info(url)
            total_tracks = min(info['total_tracks'], max_tracks) if max_tracks else info['total_tracks']
            
            self.log(f"📋 Playlist: {info['name']}")
            self.log(f"👤 Owner: {info['owner']}")
            self.log(f"🎵 Tracks to download: {total_tracks}")
            
            # Download with custom progress callback
            playlist_info, results = self.bot.downloader.download_playlist(
                url, max_tracks=max_tracks, use_async=False
            )
            
            # Show results
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            
            self.log(f"✅ Download completed: {successful} successful, {failed} failed")
            self.progress_var.set(100)
            
            if successful > 0:
                messagebox.showinfo("Success", f"Downloaded {successful} tracks successfully!")
            
        except Exception as e:
            raise e
    
    def download_album(self, url):
        """Download album"""
        self.log("💿 Downloading album...")
        results = self.bot.download_album(url, use_async=False, show_summary=False)
        
        successful = sum(1 for r in results if r.success)
        self.log(f"✅ Album download completed: {successful} tracks")
        self.progress_var.set(100)
        
        if successful > 0:
            messagebox.showinfo("Success", f"Downloaded {successful} tracks from album!")
    
    def download_track(self, url):
        """Download single track"""
        self.log("🎤 Downloading single track...")
        success = self.bot.download_track(url, show_summary=False)
        
        if success:
            self.log("✅ Track downloaded successfully")
            self.progress_var.set(100)
            messagebox.showinfo("Success", "Track downloaded successfully!")
        else:
            raise Exception("Failed to download track")
    
    def download_search(self, query):
        """Download from search query"""
        self.log(f"🔍 Searching for: {query}")
        success = self.bot.search_and_download(query, limit=1, show_summary=False)
        
        if success:
            self.log("✅ Search and download completed")
            self.progress_var.set(100)
            messagebox.showinfo("Success", "Track found and downloaded!")
        else:
            raise Exception("No tracks found for search query")
    
    def show_help(self):
        """Show help dialog"""
        help_text = """🎵 SpotyBot Help

📖 How to use:
1. Paste any Spotify URL (playlist, album, or track)
2. Choose your download folder
3. Adjust settings as needed
4. Click Download!

🔗 Supported URLs:
• Playlists: https://open.spotify.com/playlist/...
• Albums: https://open.spotify.com/album/...  
• Tracks: https://open.spotify.com/track/...
• Or just type a song name to search!

📁 Folder Organization:
• Playlists: Downloaded to "Download Folder/Playlist Name/"
• Albums: Downloaded to "Download Folder/Album Name/"
• Single Tracks: Downloaded directly to "Download Folder/"

⚙️ Settings:
• Quality: Higher = better sound, larger files
• Concurrent: More = faster downloads (don't exceed 8)
• Metadata: Adds song info and album art
• Lyrics: Downloads lyric files (.lrc)

💡 Tips:
• Use "Max Tracks" to limit playlist downloads
• Enable "Skip Existing" to avoid re-downloads
• Lower quality = faster downloads
• Save settings to remember your preferences

🎵 Happy downloading!"""
        
        messagebox.showinfo("Help", help_text)


def main():
    """Main function to run the GUI"""
    try:
        root = tk.Tk()
        app = SpotyBotGUI(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Could not start SpotyBot GUI: {e}")


if __name__ == "__main__":
    main()