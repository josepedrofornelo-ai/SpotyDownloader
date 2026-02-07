"""
Download manager using spotDL library
"""

import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
import os

from spotdl import Spotdl
from spotdl.types.song import Song
from spotdl.types.options import DownloaderOptions
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console

from .config import Config
from .spotify_client import SpotifyClient


logger = logging.getLogger(__name__)
console = Console()


class DownloadResult:
    """Result of a single download operation"""
    
    def __init__(self, track_info: Dict[str, Any], success: bool, file_path: Optional[Path] = None, error: Optional[str] = None):
        self.track_info = track_info
        self.success = success
        self.file_path = file_path
        self.error = error
        self.track_name = f"{track_info.get('main_artist', 'Unknown')} - {track_info.get('name', 'Unknown')}"


class SpotifyDownloader:
    """Spotify playlist downloader using spotDL"""
    
    def __init__(self, config: Config):
        """Initialize downloader with configuration"""
        self.config = config
        self.spotify_client = SpotifyClient(config)
        
        # Ensure output directory exists
        self.config.output_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize spotDL with configuration
        spotdl_options = config.get_spotdl_options()
        self.spotdl = Spotdl(
            client_id=config.spotify_client_id,
            client_secret=config.spotify_client_secret,
            downloader_settings=spotdl_options
        )
        
        logger.info(f"Downloader initialized with output directory: {self.config.output_directory}")
        logger.info(f"Using audio provider: {self.config.audio_provider}")
    
    def _track_to_song(self, track_info: Dict[str, Any]) -> Song:
        """Convert track info dictionary to spotDL Song object"""
        try:
            # Create Song object from Spotify track info
            song = Song.from_missing_data(
                name=track_info["name"],
                artists=track_info["artists"],
                artist=track_info["main_artist"],
                album_name=track_info["album_name"],
                album_artist=track_info.get("album_artist", track_info["main_artist"]),
                duration=track_info.get("duration_ms", 0) // 1000,  # Convert to seconds
                year=track_info.get("release_date", "")[:4] if track_info.get("release_date") else None,
                date=track_info.get("release_date", ""),
                track_number=track_info.get("track_number", 0),
                disc_number=track_info.get("disc_number", 1),
                explicit=track_info.get("explicit", False),
                url=track_info["spotify_url"],
            )
            
            return song
            
        except Exception as e:
            logger.error(f"Error converting track to Song object: {e}")
            raise
    
    def _check_existing_file(self, track_info: Dict[str, Any]) -> Optional[Path]:
        """Check if track already exists in output directory"""
        if not self.config.skip_existing_files:
            return None
        
        # Generate expected filename
        template = self.config.output_template
        filename = template.format(
            artists=" & ".join(track_info["artists"]),
            title=track_info["name"],
            album=track_info["album_name"],
            **{"output-ext": self.config.download_format}
        )
        
        # Clean filename for filesystem
        filename = self._clean_filename(filename)
        file_path = self.config.output_directory / filename
        
        if file_path.exists():
            logger.info(f"File already exists, skipping: {filename}")
            return file_path
        
        return None
    
    def _clean_filename(self, filename: str) -> str:
        """Clean filename for filesystem compatibility"""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        
        # Limit filename length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    def _create_collection_folder(self, collection_name: str) -> Path:
        """Create a subfolder for a playlist or album"""
        # Clean the collection name for filesystem
        clean_name = self._clean_filename(collection_name)
        
        # Create the subfolder path
        folder_path = self.config.output_directory / clean_name
        
        # Create the folder if it doesn't exist
        folder_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created/using collection folder: {folder_path}")
        return folder_path
    
    def _move_file_to_folder(self, file_path: Path, target_folder: Path) -> Path:
        """Move a downloaded file to a target folder"""
        try:
            if file_path and file_path.exists():
                target_path = target_folder / file_path.name
                # Move the file
                file_path.rename(target_path)
                logger.debug(f"Moved {file_path.name} to {target_folder}")
                return target_path
            return file_path
        except Exception as e:
            logger.warning(f"Could not move file {file_path}: {e}")
            return file_path
    
    def download_track(self, track_info: Dict[str, Any]) -> DownloadResult:
        """Download a single track"""
        try:
            track_name = f"{track_info.get('main_artist', 'Unknown')} - {track_info.get('name', 'Unknown')}"
            
            # Check if file already exists
            existing_file = self._check_existing_file(track_info)
            if existing_file:
                return DownloadResult(track_info, True, existing_file)
            
            # Convert to Song object
            song = self._track_to_song(track_info)
            
            # Download the song using spotDL's synchronous method
            logger.info(f"Downloading: {track_name}")
            
            # Use spotDL's download_songs method which handles the async internally
            results = self.spotdl.download_songs([song])
            
            if results and len(results) > 0:
                song_result, file_path = results[0]
                if file_path and file_path.exists():
                    logger.info(f"Successfully downloaded: {track_name} -> {file_path}")
                    return DownloadResult(track_info, True, file_path)
            
            error_msg = f"Download failed: {track_name}"
            logger.error(error_msg)
            return DownloadResult(track_info, False, error=error_msg)
        
        except Exception as e:
            error_msg = f"Error downloading {track_name}: {str(e)}"
            logger.error(error_msg)
            return DownloadResult(track_info, False, error=error_msg)
    
    def download_tracks_batch(self, tracks: List[Dict[str, Any]], progress_callback=None) -> List[DownloadResult]:
        """Download multiple tracks with progress tracking"""
        results = []
        total_tracks = len(tracks)
        
        logger.info(f"Starting download of {total_tracks} tracks")
        
        if self.config.show_progress and not progress_callback:
            console.print(f"[bold blue]🎵 Starting download of {total_tracks} tracks...[/bold blue]")
        
        # Simple loop with console output
        for i, track in enumerate(tracks, 1):
            result = self.download_track(track)
            results.append(result)
            
            if progress_callback:
                progress_callback(i, total_tracks, result)
            elif self.config.show_progress:
                status = "✅" if result.success else "❌"
                console.print(f"{status} [{i}/{total_tracks}] {result.track_name}")
            
            logger.info(f"Progress: {i}/{total_tracks}")
        
        # Summary
        successful = sum(1 for r in results if r.success)
        failed = total_tracks - successful
        
        logger.info(f"Download completed: {successful} successful, {failed} failed")
        
        return results
    
    def download_tracks_sync(self, tracks: List[Dict[str, Any]]) -> List[DownloadResult]:
        """Download tracks synchronously using spotDL's built-in batch processing"""
        total_tracks = len(tracks)
        logger.info(f"Starting synchronous download of {total_tracks} tracks")
        
        if self.config.show_progress:
            console.print(f"[bold blue]🎵 Starting download of {total_tracks} tracks...[/bold blue]")
        
        # Convert all tracks to Song objects
        songs = []
        track_map = {}
        
        for i, track_info in enumerate(tracks):
            try:
                song = self._track_to_song(track_info)
                songs.append(song)
                track_map[i] = track_info
            except Exception as e:
                logger.error(f"Error converting track to song: {e}")
                continue
        
        results = []
        
        try:
            # Use spotDL's download_songs method which handles everything internally
            download_results = self.spotdl.download_songs(songs)
            
            # Process results
            for i, (song_result, file_path) in enumerate(download_results):
                if i in track_map:
                    track_info = track_map[i]
                    track_name = f"{track_info.get('main_artist', 'Unknown')} - {track_info.get('name', 'Unknown')}"
                    
                    if file_path and file_path.exists():
                        result = DownloadResult(track_info, True, file_path)
                        status = "✅"
                        logger.info(f"Successfully downloaded: {track_name} -> {file_path}")
                    else:
                        result = DownloadResult(track_info, False, error="Download failed")
                        status = "❌"
                        logger.error(f"Failed to download: {track_name}")
                    
                    results.append(result)
                    
                    if self.config.show_progress:
                        console.print(f"{status} [{len(results)}/{total_tracks}] {result.track_name}")
            
        except Exception as e:
            logger.error(f"Batch download failed: {e}")
            # If batch fails, mark all tracks as failed
            for i, track_info in enumerate(tracks):
                result = DownloadResult(track_info, False, error=str(e))
                results.append(result)
                
                if self.config.show_progress:
                    console.print(f"❌ [{len(results)}/{total_tracks}] {result.track_name}")
        
        successful = sum(1 for r in results if r.success)
        failed = total_tracks - successful
        logger.info(f"Download completed: {successful} successful, {failed} failed")
        
        return results
    
    def download_playlist(self, playlist_url: str, max_tracks: Optional[int] = None, use_async: bool = True) -> Tuple[Dict[str, Any], List[DownloadResult]]:
        """
        Download entire Spotify playlist
        
        Args:
            playlist_url: Spotify playlist URL
            max_tracks: Maximum number of tracks to download (None for all)
            use_async: Whether to use async downloads
        
        Returns:
            Tuple of (playlist_info, download_results)
        """
        try:
            # Get playlist information
            playlist_info = self.spotify_client.get_playlist_info(playlist_url)
            playlist_name = playlist_info['name']
            logger.info(f"Starting download of playlist: {playlist_name}")
            logger.info(f"Total tracks in playlist: {playlist_info['total_tracks']}")
            
            # Create subfolder for this playlist
            playlist_folder = self._create_collection_folder(playlist_name)
            
            # Get tracks
            tracks = self.spotify_client.get_playlist_tracks(playlist_url, limit=max_tracks)
            
            if not tracks:
                logger.warning("No tracks found in playlist")
                return playlist_info, []
            
            logger.info(f"Downloading {len(tracks)} tracks to: {playlist_folder}")
            
            # Download tracks to main output directory
            results = self.download_tracks_sync(tracks)
            
            # Move downloaded files to playlist subfolder
            for result in results:
                if result.success and result.file_path:
                    new_path = self._move_file_to_folder(result.file_path, playlist_folder)
                    result.file_path = new_path
            
            return playlist_info, results
            
        except Exception as e:
            logger.error(f"Error downloading playlist: {e}")
            raise
    
    def download_album(self, album_url: str, use_async: bool = True) -> List[DownloadResult]:
        """Download entire Spotify album"""
        try:
            # Get album tracks
            tracks = self.spotify_client.get_album_tracks(album_url)
            
            if not tracks:
                logger.warning("No tracks found in album")
                return []
            
            # Get album name from first track
            album_name = tracks[0].get('album_name', 'Unknown Album')
            logger.info(f"Starting download of album: {album_name}")
            
            # Create subfolder for this album
            album_folder = self._create_collection_folder(album_name)
            
            logger.info(f"Downloading {len(tracks)} tracks to: {album_folder}")
            
            # Download tracks to main output directory
            results = self.download_tracks_sync(tracks)
            
            # Move downloaded files to album subfolder
            for result in results:
                if result.success and result.file_path:
                    new_path = self._move_file_to_folder(result.file_path, album_folder)
                    result.file_path = new_path
            
            return results
            
        except Exception as e:
            logger.error(f"Error downloading album: {e}")
            raise