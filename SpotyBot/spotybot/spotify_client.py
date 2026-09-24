"""
Spotify API client for fetching playlist data
"""

import logging
from typing import List, Dict, Any, Optional
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from .config import Config


logger = logging.getLogger(__name__)


class SpotifyClient:
    """Spotify API client wrapper"""
    
    def __init__(self, config: Config):
        """Initialize Spotify client with credentials"""
        self.config = config
        
        if not config.validate_spotify_credentials():
            raise ValueError("Spotify credentials not configured. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
        
        # Set up Spotify client credentials
        client_credentials_manager = SpotifyClientCredentials(
            client_id=config.spotify_client_id,
            client_secret=config.spotify_client_secret
        )
        
        self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        logger.info("Spotify client initialized successfully")
    
    def extract_playlist_id(self, url: str) -> str:
        """Extract playlist ID from Spotify URL"""
        if "playlist/" in url:
            # Extract ID from various URL formats
            if "?" in url:
                url = url.split("?")[0]  # Remove query parameters
            playlist_id = url.split("playlist/")[-1]
            return playlist_id
        elif len(url) == 22 and not "/" in url:
            # Already a playlist ID
            return url
        else:
            raise ValueError(f"Invalid Spotify playlist URL: {url}")
    
    def get_playlist_info(self, playlist_url: str) -> Dict[str, Any]:
        """Get basic playlist information"""
        try:
            playlist_id = self.extract_playlist_id(playlist_url)
            playlist = self.spotify.playlist(playlist_id, fields="name,description,owner,external_urls,images,tracks(total)")
            
            return {
                "id": playlist_id,
                "name": playlist["name"],
                "description": playlist.get("description", ""),
                "owner": playlist["owner"]["display_name"],
                "url": playlist["external_urls"]["spotify"],
                "total_tracks": playlist["tracks"]["total"],
                "cover_url": playlist["images"][0]["url"] if playlist["images"] else None
            }
        except Exception as e:
            logger.error(f"Error fetching playlist info: {e}")
            raise
    
    def get_playlist_tracks(self, playlist_url: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all tracks from a Spotify playlist
        
        Args:
            playlist_url: Spotify playlist URL or ID
            limit: Maximum number of tracks to fetch (None for all tracks)
        
        Returns:
            List of track dictionaries with metadata
        """
        try:
            playlist_id = self.extract_playlist_id(playlist_url)
            
            logger.info(f"Fetching tracks from playlist: {playlist_id}")
            
            tracks = []
            offset = 0
            batch_size = 100  # Maximum allowed by Spotify API
            
            while True:
                # Fetch tracks in batches
                results = self.spotify.playlist_tracks(
                    playlist_id,
                    offset=offset,
                    limit=min(batch_size, (limit - len(tracks)) if limit else batch_size),
                    fields="items(track(id,name,artists,album,external_urls,duration_ms,explicit,preview_url)),next"
                )
                
                batch_tracks = []
                for item in results["items"]:
                    if item["track"] and item["track"]["id"]:  # Skip null or local tracks
                        track = item["track"]
                        
                        # Extract artist information
                        artists = [artist["name"] for artist in track["artists"]]
                        main_artist = artists[0] if artists else "Unknown Artist"
                        
                        # Extract album information
                        album = track.get("album", {})
                        
                        track_info = {
                            "id": track["id"],
                            "name": track["name"],
                            "artists": artists,
                            "main_artist": main_artist,
                            "album_name": album.get("name", "Unknown Album"),
                            "album_artist": album.get("artists", [{}])[0].get("name", main_artist),
                            "release_date": album.get("release_date", ""),
                            "duration_ms": track.get("duration_ms", 0),
                            "explicit": track.get("explicit", False),
                            "preview_url": track.get("preview_url"),
                            "spotify_url": track["external_urls"]["spotify"],
                            "track_number": track.get("track_number", 0),
                            "disc_number": track.get("disc_number", 1),
                        }
                        
                        batch_tracks.append(track_info)
                        
                        # Check if we've reached the limit
                        if limit and len(tracks) + len(batch_tracks) >= limit:
                            batch_tracks = batch_tracks[:limit - len(tracks)]
                            break
                
                tracks.extend(batch_tracks)
                
                logger.info(f"Fetched {len(tracks)} tracks so far...")
                
                # Check if there are more tracks and we haven't reached limit
                if not results["next"] or (limit and len(tracks) >= limit):
                    break
                
                offset += batch_size
            
            # Add 1-based playlist position and list length to every track
            total = len(tracks)
            for i, track in enumerate(tracks):
                track["playlist_position"] = i + 1
                track["list_length"] = total

            logger.info(f"Successfully fetched {total} tracks from playlist")
            return tracks
            
        except Exception as e:
            logger.error(f"Error fetching playlist tracks: {e}")
            raise
    
    def search_track(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for tracks on Spotify"""
        try:
            results = self.spotify.search(q=query, type="track", limit=limit)
            tracks = []
            
            for track in results["tracks"]["items"]:
                artists = [artist["name"] for artist in track["artists"]]
                album = track.get("album", {})
                
                track_info = {
                    "id": track["id"],
                    "name": track["name"],
                    "artists": artists,
                    "main_artist": artists[0] if artists else "Unknown Artist",
                    "album_name": album.get("name", "Unknown Album"),
                    "spotify_url": track["external_urls"]["spotify"],
                    "duration_ms": track.get("duration_ms", 0),
                    "explicit": track.get("explicit", False),
                    "preview_url": track.get("preview_url")
                }
                
                tracks.append(track_info)
            
            return tracks
            
        except Exception as e:
            logger.error(f"Error searching for tracks: {e}")
            raise
    
    def get_album_tracks(self, album_url: str) -> List[Dict[str, Any]]:
        """Get all tracks from a Spotify album"""
        try:
            album_id = album_url.split("album/")[-1].split("?")[0]
            
            # Get album info first
            album_info = self.spotify.album(album_id)
            
            tracks = []
            for track in album_info["tracks"]["items"]:
                artists = [artist["name"] for artist in track["artists"]]
                
                track_info = {
                    "id": track["id"],
                    "name": track["name"],
                    "artists": artists,
                    "main_artist": artists[0] if artists else "Unknown Artist",
                    "album_name": album_info["name"],
                    "album_artist": album_info["artists"][0]["name"],
                    "release_date": album_info["release_date"],
                    "spotify_url": track["external_urls"]["spotify"],
                    "track_number": track["track_number"],
                    "disc_number": track["disc_number"],
                    "duration_ms": track["duration_ms"],
                    "explicit": track["explicit"]
                }
                
                tracks.append(track_info)
            
            logger.info(f"Fetched {len(tracks)} tracks from album: {album_info['name']}")
            return tracks
            
        except Exception as e:
            logger.error(f"Error fetching album tracks: {e}")
            raise