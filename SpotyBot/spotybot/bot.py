"""
Main SpotyBot application
"""

import logging
import sys
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.logging import RichHandler

from .config import Config
from .spotify_client import SpotifyClient
from .downloader import SpotifyDownloader, DownloadResult


# Set up rich console
console = Console()


class SpotyBot:
    """Main SpotyBot application class"""
    
    def __init__(self, config: Optional[Config] = None, config_file: Optional[str] = None):
        """Initialize SpotyBot"""
        
        # Load configuration
        if config:
            self.config = config
        else:
            self.config = Config.from_env(config_file)
        
        # Set up logging
        self._setup_logging()
        
        # Initialize components
        try:
            self.spotify_client = SpotifyClient(self.config)
            self.downloader = SpotifyDownloader(self.config)
            
            self.logger.info("SpotyBot initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SpotyBot: {e}")
            raise
    
    def _setup_logging(self):
        """Configure logging with rich handler"""
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(console=console, show_path=False)]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def print_banner(self):
        """Print SpotyBot banner"""
        banner = r"""
 ____                  _         ____        _   
/ ___| _ __   ___  __ _| |_ _   _| __ )  ___ | |_ 
\___ \| '_ \ / _ \/ _` | __| | | |  _ \ / _ \| __|
 ___) | |_) | (_) | (_| | |_| |_| | |_) | (_) | |_ 
|____/| .__/ \___/ \__,_|\__|\__, |____/ \___/ \__|
      |_|                   |___/                 

🎵 Spotify Playlist Downloader using spotDL 🎵
        """
        
        console.print(Panel.fit(banner, border_style="bright_magenta", padding=(1, 2)))
    
    def print_config_summary(self):
        """Print configuration summary"""
        table = Table(title="Configuration", show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        table.add_row("Output Directory", str(self.config.output_directory))
        table.add_row("Audio Format", self.config.download_format)
        table.add_row("Audio Quality", self.config.download_quality)
        table.add_row("Audio Provider", self.config.audio_provider)
        table.add_row("Max Concurrent", str(self.config.max_concurrent_downloads))
        table.add_row("Skip Existing", "✓" if self.config.skip_existing_files else "✗")
        table.add_row("Embed Metadata", "✓" if self.config.embed_metadata else "✗")
        table.add_row("Download Lyrics", "✓" if self.config.download_lyrics else "✗")
        
        console.print(table)
    
    def download_playlist(self, playlist_url: str, max_tracks: Optional[int] = None, 
                         use_async: bool = True, show_summary: bool = True) -> bool:
        """
        Download a Spotify playlist
        
        Args:
            playlist_url: Spotify playlist URL
            max_tracks: Maximum number of tracks to download
            use_async: Whether to use async downloads
            show_summary: Whether to show download summary
        
        Returns:
            True if download was successful, False otherwise
        """
        try:
            console.print(f"\n[bold blue]🎵 Processing playlist: {playlist_url}[/bold blue]")
            
            # Download playlist
            playlist_info, results = self.downloader.download_playlist(
                playlist_url, max_tracks=max_tracks, use_async=use_async
            )
            
            if show_summary:
                self._show_download_summary(playlist_info, results)
            
            # Return success status
            return len(results) > 0 and any(r.success for r in results)
            
        except Exception as e:
            console.print(f"[bold red]❌ Error downloading playlist: {e}[/bold red]")
            self.logger.error(f"Playlist download failed: {e}", exc_info=True)
            return False
    
    def download_album(self, album_url: str, use_async: bool = True, show_summary: bool = True, progress_callback=None) -> bool:
        """
        Download a Spotify album
        
        Args:
            album_url: Spotify album URL
            use_async: Whether to use async downloads
            show_summary: Whether to show download summary
            progress_callback: optional callable(done, total, track_name)
        
        Returns:
            True if download was successful, False otherwise
        """
        try:
            console.print(f"\n[bold blue]💿 Processing album: {album_url}[/bold blue]")
            
            # Download album
            results = self.downloader.download_album(album_url, use_async=use_async, progress_callback=progress_callback)
            
            if show_summary:
                self._show_download_summary({"name": "Album", "total_tracks": len(results)}, results)
            
            # Return success status
            return len(results) > 0 and any(r.success for r in results)
            
        except Exception as e:
            console.print(f"[bold red]❌ Error downloading album: {e}[/bold red]")
            self.logger.error(f"Album download failed: {e}", exc_info=True)
            return False
    
    def download_track(self, track_url: str, show_summary: bool = True) -> bool:
        """
        Download a single Spotify track
        
        Args:
            track_url: Spotify track URL
            show_summary: Whether to show download summary
        
        Returns:
            True if download was successful, False otherwise
        """
        try:
            console.print(f"\n[bold blue]🎤 Processing track: {track_url}[/bold blue]")
            
            # Extract track ID and search for track info
            track_id = track_url.split("track/")[-1].split("?")[0]
            track_info = self.spotify_client.spotify.track(track_id)
            
            # Convert to our track format
            artists = [artist["name"] for artist in track_info["artists"]]
            album = track_info.get("album", {})
            
            track_data = {
                "id": track_info["id"],
                "name": track_info["name"],
                "artists": artists,
                "main_artist": artists[0] if artists else "Unknown Artist",
                "album_name": album.get("name", "Unknown Album"),
                "album_artist": album.get("artists", [{}])[0].get("name", artists[0] if artists else "Unknown"),
                "release_date": album.get("release_date", ""),
                "duration_ms": track_info.get("duration_ms", 0),
                "explicit": track_info.get("explicit", False),
                "spotify_url": track_info["external_urls"]["spotify"],
                "track_number": track_info.get("track_number", 0),
                "disc_number": track_info.get("disc_number", 1),
            }
            
            # Download the track
            result = self.downloader.download_track(track_data)
            
            if show_summary:
                self._show_download_summary(
                    {"name": "Single Track", "total_tracks": 1}, 
                    [result]
                )
            
            return result.success
            
        except Exception as e:
            console.print(f"[bold red]❌ Error downloading track: {e}[/bold red]")
            self.logger.error(f"Track download failed: {e}", exc_info=True)
            return False
    
    def search_and_download(self, search_query: str, limit: int = 1, show_summary: bool = True) -> bool:
        """
        Search for tracks and download them
        
        Args:
            search_query: Search query string
            limit: Number of tracks to download
            show_summary: Whether to show download summary
        
        Returns:
            True if download was successful, False otherwise
        """
        try:
            console.print(f"\n[bold blue]🔍 Searching for: {search_query}[/bold blue]")
            
            # Search for tracks
            search_results = self.spotify_client.search_track(search_query, limit=limit)
            
            if not search_results:
                console.print("[bold red]❌ No tracks found[/bold red]")
                return False
            
            console.print(f"[bold green]✓ Found {len(search_results)} track(s)[/bold green]")
            
            # Download found tracks
            results = []
            for track_data in search_results:
                result = self.downloader.download_track(track_data)
                results.append(result)
            
            if show_summary:
                self._show_download_summary(
                    {"name": f"Search: {search_query}", "total_tracks": len(results)}, 
                    results
                )
            
            return any(r.success for r in results)
            
        except Exception as e:
            console.print(f"[bold red]❌ Error searching and downloading: {e}[/bold red]")
            self.logger.error(f"Search and download failed: {e}", exc_info=True)
            return False
    
    def _show_download_summary(self, playlist_info: dict, results: List[DownloadResult]):
        """Show download results summary"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        # Summary panel
        summary_text = f"""
[bold green]✅ Successfully downloaded: {len(successful)} tracks[/bold green]
[bold red]❌ Failed downloads: {len(failed)} tracks[/bold red]
[bold blue]📁 Output directory: {self.config.output_directory}[/bold blue]
        """
        
        console.print(Panel(
            summary_text.strip(),
            title=f"📊 Download Summary - {playlist_info['name']}",
            border_style="bright_green" if len(failed) == 0 else "yellow"
        ))
        
        # Failed downloads table
        if failed and self.config.log_level.upper() in ["DEBUG", "INFO"]:
            table = Table(title="❌ Failed Downloads", show_header=True, header_style="bold red")
            table.add_column("Track", style="cyan")
            table.add_column("Error", style="red")
            
            for result in failed[:10]:  # Show max 10 failed downloads
                table.add_row(
                    result.track_name,
                    result.error or "Unknown error"
                )
            
            if len(failed) > 10:
                table.add_row("...", f"and {len(failed) - 10} more")
            
            console.print(table)
    
    def get_playlist_info(self, playlist_url: str) -> dict:
        """Get information about a playlist without downloading"""
        try:
            return self.spotify_client.get_playlist_info(playlist_url)
        except Exception as e:
            self.logger.error(f"Error getting playlist info: {e}")
            raise
    
    def validate_url(self, url: str) -> tuple:
        """
        Validate and identify Spotify URL type
        
        Returns:
            Tuple of (url_type, is_valid) where url_type is one of:
            'playlist', 'album', 'track', 'unknown'
        """
        if "spotify.com" not in url and "open.spotify.com" not in url:
            return "unknown", False
        
        if "playlist/" in url:
            return "playlist", True
        elif "album/" in url:
            return "album", True
        elif "track/" in url:
            return "track", True
        else:
            return "unknown", False
    
    def run_interactive(self):
        """Run interactive mode"""
        self.print_banner()
        console.print("[bold cyan]Welcome to SpotyBot Interactive Mode![/bold cyan]")
        console.print("Enter Spotify URLs or search queries. Type 'help' for commands, 'quit' to exit.\n")
        
        self.print_config_summary()
        
        while True:
            try:
                user_input = console.input("\n[bold cyan]SpotyBot>[/bold cyan] ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    console.print("[bold green]👋 Goodbye![/bold green]")
                    break
                
                elif user_input.lower() in ['help', 'h']:
                    self._show_help()
                
                elif user_input.lower() in ['config', 'settings']:
                    self.print_config_summary()
                
                elif user_input.startswith("search "):
                    query = user_input[7:].strip()
                    if query:
                        self.search_and_download(query)
                    else:
                        console.print("[bold red]Please provide a search query[/bold red]")
                
                else:
                    # Try to process as URL
                    url_type, is_valid = self.validate_url(user_input)
                    
                    if is_valid:
                        if url_type == "playlist":
                            self.download_playlist(user_input)
                        elif url_type == "album":
                            self.download_album(user_input)
                        elif url_type == "track":
                            self.download_track(user_input)
                    else:
                        # Try as search query
                        console.print(f"[yellow]🔍 Treating as search query: {user_input}[/yellow]")
                        self.search_and_download(user_input)
                        
            except KeyboardInterrupt:
                console.print("\n[bold green]👋 Goodbye![/bold green]")
                break
            except Exception as e:
                console.print(f"[bold red]❌ Error: {e}[/bold red]")
                self.logger.error(f"Interactive mode error: {e}", exc_info=True)
    
    def _show_help(self):
        """Show help information"""
        help_text = """
[bold cyan]📖 SpotyBot Commands:[/bold cyan]

[bold green]URLs:[/bold green]
• Paste any Spotify URL (playlist, album, or track)
• Example: https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M

[bold green]Search:[/bold green]
• search <query> - Search and download tracks
• Example: search The Beatles Hey Jude

[bold green]Commands:[/bold green]
• help, h - Show this help
• config, settings - Show current configuration
• quit, exit, q - Exit the program

[bold green]Tips:[/bold green]
• Any text without a command will be treated as a search query
• Use Ctrl+C to interrupt current download
• Check your output directory for downloaded files
        """
        
        console.print(Panel(help_text.strip(), title="📖 Help", border_style="bright_blue"))