"""
Download manager using spotDL library
"""

import logging
import asyncio
import shutil
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
        self.spotdl = None  # Lazily initialized inside the download thread
        
        # Ensure output directory exists
        self.config.output_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Downloader initialized with output directory: {self.config.output_directory}")
        logger.info(f"Using audio provider: {self.config.audio_provider}")
        logger.info(f"Lyrics download: {'enabled' if self.config.download_lyrics else 'disabled'}")
    
    def _ensure_spotdl(self):
        """Initialize spotDL if not already done, and register its event loop as the
        *current thread's* event loop.

        The GUI processes each queued download in a fresh worker thread, but
        `self.spotdl` (and its internal event loop) is only created once and reused.
        asyncio's "current event loop" is thread-local, so every new thread must call
        `asyncio.set_event_loop()` with spotDL's loop before calling into spotDL,
        otherwise spotDL's internal async code raises
        "There is no current event loop in thread ...".
        """
        if self.spotdl is not None:
            asyncio.set_event_loop(self.spotdl.downloader.loop)
            return

        # Create and set a fresh event loop for this thread so spotDL's internal
        # asyncio machinery attaches to the correct loop.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        spotdl_options = self.config.get_spotdl_options()
        self.spotdl = Spotdl(
            client_id=self.config.spotify_client_id,
            client_secret=self.config.spotify_client_secret,
            downloader_settings=spotdl_options
        )
        logger.debug(f"spotDL initialized with generate_lrc={spotdl_options.get('generate_lrc', False)}")
    
    def _add_position_prefix(self, file_path: Path, position: int, total: int) -> Path:
        """Rename a downloaded file to add a zero-padded position prefix.

        E.g.  position=3, total=75  →  '03 - original_name.mp3'
        """
        if not file_path or not file_path.exists():
            return file_path
        try:
            padding = len(str(total))
            prefix = str(position).zfill(padding)
            new_name = f"{prefix} - {file_path.name}"
            new_path = file_path.parent / new_name
            if new_path.exists():
                new_path.unlink()
            file_path.rename(new_path)
            logger.debug(f"Renamed to: {new_name}")
            return new_path
        except Exception as e:
            logger.warning(f"Could not rename file {file_path}: {e}")
            return file_path

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
        """Move a downloaded file to a target folder, including related files like lyrics"""
        try:
            if file_path and file_path.exists():
                target_path = target_folder / file_path.name
                
                # If target exists, remove it first to avoid errors
                if target_path.exists():
                    target_path.unlink()
                    logger.debug(f"Removed existing file: {target_path}")
                
                # Use shutil.move for robust file moving
                moved_path = shutil.move(str(file_path), str(target_path))
                logger.info(f"Moved {file_path.name} to {target_folder}")
                
                # Also move any related files (e.g., .lrc lyrics files) if enabled
                if self.config.download_lyrics:
                    base_name = file_path.stem
                    parent_dir = file_path.parent
                    for related_file in parent_dir.glob(f"{base_name}.*"):
                        if related_file != file_path and related_file.exists():
                            related_target = target_folder / related_file.name
                            if related_target.exists():
                                related_target.unlink()
                            shutil.move(str(related_file), str(related_target))
                            logger.debug(f"Moved related file {related_file.name} to {target_folder}")
                else:
                    # Clean up any .lrc files that might have been created despite settings
                    base_name = file_path.stem
                    parent_dir = file_path.parent
                    for lrc_file in parent_dir.glob(f"{base_name}.lrc"):
                        if lrc_file.exists():
                            lrc_file.unlink()
                            logger.debug(f"Removed unwanted lyrics file: {lrc_file.name}")
                
                return Path(moved_path)
            else:
                logger.warning(f"File not found for moving: {file_path}")
                return file_path
        except Exception as e:
            logger.error(f"Failed to move file {file_path}: {e}")
            return file_path
    
    def download_track(self, track_info: Dict[str, Any]) -> DownloadResult:
        """Download a single track"""
        try:
            track_name = f"{track_info.get('main_artist', 'Unknown')} - {track_info.get('name', 'Unknown')}"
            
            # Check if file already exists
            existing_file = self._check_existing_file(track_info)
            if existing_file:
                return DownloadResult(track_info, True, existing_file)
            
            # Initialize spotDL inside this thread (creates the correct event loop)
            self._ensure_spotdl()

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
                elif file_path is None:
                    # spotDL returns None when a file is skipped (already exists on disk).
                    # Try our own pre-check first, then do a broader title search.
                    existing = self._check_existing_file(track_info)
                    if existing:
                        logger.info(f"Track already exists, skipped by spotDL: {track_name} -> {existing}")
                        return DownloadResult(track_info, True, existing)
                    # Broader glob search using the track name in the output directory
                    clean_title = self._clean_filename(track_info.get('name', ''))
                    for candidate in self.config.output_directory.rglob(f"*{clean_title}*"):
                        if candidate.is_file():
                            logger.info(f"Found existing file for {track_name}: {candidate}")
                            return DownloadResult(track_info, True, candidate)
            
            error_msg = f"Download failed: {track_name}"
            logger.error(error_msg)
            return DownloadResult(track_info, False, error=error_msg)
        
        except Exception as e:
            error_msg = f"Error downloading {track_name}: {str(e)}"
            logger.error(error_msg)
            return DownloadResult(track_info, False, error=error_msg)
    
    def _process_batch_results(
        self,
        batch_tracks: List[Dict[str, Any]],
        batch_download: list,
    ) -> List[DownloadResult]:
        """Convert raw spotDL batch results into DownloadResult objects."""
        results = []
        for j, (song_result, file_path) in enumerate(batch_download):
            track_info = batch_tracks[j] if j < len(batch_tracks) else {}
            track_name = f"{track_info.get('main_artist', 'Unknown')} - {track_info.get('name', 'Unknown')}"

            if file_path and file_path.exists():
                result = DownloadResult(track_info, True, file_path)
                logger.info(f"Downloaded: {track_name} -> {file_path}")
            elif file_path is None:
                existing = self._check_existing_file(track_info)
                if not existing:
                    clean_title = self._clean_filename(track_info.get('name', ''))
                    candidates = list(self.config.output_directory.rglob(f"*{clean_title}*"))
                    existing = next((c for c in candidates if c.is_file()), None)
                if existing:
                    result = DownloadResult(track_info, True, existing)
                    logger.info(f"Already exists, skipped: {track_name}")
                else:
                    result = DownloadResult(track_info, False, error="Download failed (file not found)")
                    logger.error(f"Failed: {track_name}")
            else:
                result = DownloadResult(track_info, False, error="Download failed")
                logger.error(f"Failed: {track_name}")

            results.append(result)
        return results

    def download_tracks_batch(
        self,
        tracks: List[Dict[str, Any]],
        progress_callback=None,
    ) -> List[DownloadResult]:
        """Download tracks in concurrent mini-batches with per-track progress reporting.

        Uses spotDL's own thread pool within each mini-batch (size = max_concurrent_downloads),
        so N songs are downloaded in parallel while progress is reported after each batch.

        Args:
            tracks: list of track dicts.
            progress_callback: optional callable(done: int, total: int, track_name: str)
                called after every individual track result is processed.
        """
        total_tracks = len(tracks)
        batch_size = max(1, self.config.max_concurrent_downloads)
        logger.info(f"Starting download of {total_tracks} tracks (batch_size={batch_size})")

        # Ensure spotDL is initialised inside this thread
        self._ensure_spotdl()

        if self.config.show_progress and not progress_callback:
            console.print(f"[bold blue]🎵 Starting download of {total_tracks} tracks...[/bold blue]")

        all_results: List[DownloadResult] = []
        done_count = 0

        for batch_start in range(0, total_tracks, batch_size):
            batch_tracks = tracks[batch_start:batch_start + batch_size]

            # Build Song objects for this batch
            songs = []
            valid_tracks = []
            for track_info in batch_tracks:
                try:
                    songs.append(self._track_to_song(track_info))
                    valid_tracks.append(track_info)
                except Exception as e:
                    logger.error(f"Error converting track to Song: {e}")
                    all_results.append(DownloadResult(track_info, False, error=str(e)))
                    done_count += 1
                    if progress_callback:
                        track_name = f"{track_info.get('main_artist', '?')} - {track_info.get('name', '?')}"
                        progress_callback(done_count, total_tracks, track_name)

            if not songs:
                continue

            try:
                # Download the whole mini-batch concurrently via spotDL's thread pool
                batch_download = self.spotdl.download_songs(songs)
                batch_results = self._process_batch_results(valid_tracks, batch_download)
            except Exception as e:
                logger.error(f"Batch download error: {e}")
                batch_results = [DownloadResult(t, False, error=str(e)) for t in valid_tracks]

            for result in batch_results:
                all_results.append(result)
                done_count += 1
                track_name = result.track_name
                if progress_callback:
                    progress_callback(done_count, total_tracks, track_name)
                elif self.config.show_progress:
                    status = "✅" if result.success else "❌"
                    console.print(f"{status} [{done_count}/{total_tracks}] {track_name}")

            logger.info(f"Batch done: {done_count}/{total_tracks}")

        successful = sum(1 for r in all_results if r.success)
        logger.info(f"Download completed: {successful} successful, {total_tracks - successful} failed")
        return all_results
    
    def download_tracks_sync(self, tracks: List[Dict[str, Any]]) -> List[DownloadResult]:
        """Alias kept for CLI/backwards compatibility — delegates to download_tracks_batch."""
        return self.download_tracks_batch(tracks)

    def download_playlist(
        self,
        playlist_url: str,
        max_tracks: Optional[int] = None,
        use_async: bool = True,
        progress_callback=None,
    ) -> Tuple[Dict[str, Any], List[DownloadResult]]:
        """
        Download entire Spotify playlist.

        Args:
            playlist_url: Spotify playlist URL
            max_tracks: Maximum number of tracks to download (None for all)
            use_async: Unused; kept for API compatibility
            progress_callback: optional callable(done: int, total: int, track_name: str)

        Returns:
            Tuple of (playlist_info, download_results)
        """
        try:
            playlist_info = self.spotify_client.get_playlist_info(playlist_url)
            playlist_name = playlist_info['name']
            logger.info(f"Starting download of playlist: {playlist_name}")

            playlist_folder = self._create_collection_folder(playlist_name)
            tracks = self.spotify_client.get_playlist_tracks(playlist_url, limit=max_tracks)

            if not tracks:
                logger.warning("No tracks found in playlist")
                return playlist_info, []

            total = len(tracks)
            logger.info(f"Downloading {total} tracks to: {playlist_folder}")

            # Download one-by-one so per-track callbacks work
            results = self.download_tracks_batch(tracks, progress_callback=progress_callback)

            # Rename with position prefix then move to playlist subfolder
            moved_count = 0
            for i, result in enumerate(results, 1):
                if result.success and result.file_path:
                    result.file_path = self._add_position_prefix(result.file_path, i, total)
                    new_path = self._move_file_to_folder(result.file_path, playlist_folder)
                    result.file_path = new_path
                    if new_path.parent == playlist_folder:
                        moved_count += 1

            logger.info(f"Moved {moved_count} files to playlist folder")
            return playlist_info, results

        except Exception as e:
            logger.error(f"Error downloading playlist: {e}")
            raise
    
    def download_album(
        self,
        album_url: str,
        use_async: bool = True,
        progress_callback=None,
    ) -> List[DownloadResult]:
        """Download entire Spotify album."""
        try:
            tracks = self.spotify_client.get_album_tracks(album_url)

            if not tracks:
                logger.warning("No tracks found in album")
                return []

            album_name = tracks[0].get('album_name', 'Unknown Album')
            total = len(tracks)
            logger.info(f"Starting download of album: {album_name}")

            album_folder = self._create_collection_folder(album_name)
            logger.info(f"Downloading {total} tracks to: {album_folder}")

            results = self.download_tracks_batch(tracks, progress_callback=progress_callback)

            moved_count = 0
            for i, result in enumerate(results, 1):
                if result.success and result.file_path:
                    result.file_path = self._add_position_prefix(result.file_path, i, total)
                    new_path = self._move_file_to_folder(result.file_path, album_folder)
                    result.file_path = new_path
                    if new_path.parent == album_folder:
                        moved_count += 1

            logger.info(f"Moved {moved_count} files to album folder")
            return results

        except Exception as e:
            logger.error(f"Error downloading album: {e}")
            raise