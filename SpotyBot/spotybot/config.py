"""
Configuration management for SpotyBot
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, validator
from dotenv import load_dotenv


class Config(BaseModel):
    """Configuration settings for SpotyBot"""
    
    # Spotify API
    spotify_client_id: str
    spotify_client_secret: str
    
    # Download settings
    download_format: str = "mp3"
    download_quality: str = "320k"
    output_template: str = "{artists} - {title}.{output-ext}"
    output_directory: Path = Path.home() / "Music" / "spotybot"
    
    # Audio provider settings
    audio_provider: str = "youtube-music"
    audio_providers_fallback: List[str] = ["youtube-music", "soundcloud"]
    lyrics_providers: List[str] = ["genius", "azlyrics", "musixmatch"]
    
    # Download behavior
    max_concurrent_downloads: int = 4
    skip_existing_files: bool = True
    embed_metadata: bool = True
    download_lyrics: bool = True
    overwrite_existing: str = "skip"  # skip, metadata, force
    
    # Progress and logging
    log_level: str = "INFO"
    show_progress: bool = True
    simple_ui: bool = False
    
    @validator("output_directory", pre=True)
    def validate_output_directory(cls, v):
        """Ensure output directory is a Path object"""
        if isinstance(v, str):
            return Path(v)
        return v
    
    @validator("download_format")
    def validate_format(cls, v):
        """Validate audio format"""
        valid_formats = ["mp3", "flac", "ogg", "opus", "m4a"]
        if v not in valid_formats:
            raise ValueError(f"Format must be one of {valid_formats}")
        return v
    
    @validator("download_quality")
    def validate_quality(cls, v):
        """Validate audio quality"""
        valid_qualities = ["96k", "128k", "160k", "192k", "256k", "320k"]
        if v not in valid_qualities:
            raise ValueError(f"Quality must be one of {valid_qualities}")
        return v
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        """Load configuration from environment variables"""
        if env_file and os.path.exists(env_file):
            load_dotenv(env_file)
        else:
            # Try to load .env from current directory
            load_dotenv()

        return cls(
            spotify_client_id=os.getenv("SPOTIFY_CLIENT_ID", ""),
            spotify_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET", ""),
            download_format=os.getenv("DOWNLOAD_FORMAT", "mp3"),
            download_quality=os.getenv("DOWNLOAD_QUALITY", "320k"),
            output_template=os.getenv("OUTPUT_TEMPLATE", "{artists} - {title}.{output-ext}"),
            output_directory=Path(os.getenv("OUTPUT_DIRECTORY", str(Path.home() / "Music" / "spotybot"))),
            audio_provider=os.getenv("AUDIO_PROVIDER", "youtube-music"),

            lyrics_providers=os.getenv("LYRICS_PROVIDERS", "genius,azlyrics,musixmatch").split(","),
            max_concurrent_downloads=int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "4")),
            skip_existing_files=os.getenv("SKIP_EXISTING_FILES", "true").lower() == "true",
            embed_metadata=os.getenv("EMBED_METADATA", "true").lower() == "true",
            download_lyrics=os.getenv("DOWNLOAD_LYRICS", "true").lower() == "true",
            overwrite_existing=os.getenv("OVERWRITE_EXISTING", "skip"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            show_progress=os.getenv("SHOW_PROGRESS", "true").lower() == "true",
            simple_ui=os.getenv("SIMPLE_UI", "false").lower() == "true"
        )
    
    def validate_spotify_credentials(self) -> bool:
        """Check if Spotify credentials are set"""
        return bool(self.spotify_client_id and self.spotify_client_secret)
    
    def get_spotdl_options(self) -> dict:
        """Get spotDL configuration options"""
        audio_providers = [self.audio_provider]
        for provider in self.audio_providers_fallback:
            if provider and provider not in audio_providers:
                audio_providers.append(provider)

        options = {
            "audio_providers": audio_providers,
            "output": str(self.output_directory / self.output_template),
            "format": self.download_format,
            "bitrate": self.download_quality,
            "overwrite": self.overwrite_existing,
            "threads": self.max_concurrent_downloads,
            "simple_tui": self.simple_ui,
            "log_level": self.log_level,
            "skip_explicit": False,
            "generate_lrc": self.download_lyrics,
            "print_errors": True,
        }
        
        # Only add lyrics providers if lyrics are enabled
        if self.download_lyrics:
            options["lyrics_providers"] = self.lyrics_providers
        else:
            options["lyrics_providers"] = []
            
        return options