"""
Command Line Interface for SpotyBot
"""

import sys
from pathlib import Path
from typing import Optional
import click
from rich.console import Console

from . import __version__
from .bot import SpotyBot
from .config import Config


console = Console()


@click.group(invoke_without_command=True)
@click.option("--config", "-c", type=click.Path(exists=True), help="Configuration file path")
@click.option("--output", "-o", type=click.Path(), help="Output directory for downloads")
@click.option("--format", "-f", type=click.Choice(["mp3", "flac", "ogg", "opus", "m4a"]), help="Audio format")
@click.option("--quality", "-q", type=click.Choice(["96k", "128k", "160k", "192k", "256k", "320k"]), help="Audio quality")
@click.option("--async-downloads/--sync-downloads", default=True, help="Use async downloads")
@click.option("--max-concurrent", "-j", type=int, help="Maximum concurrent downloads")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--quiet", is_flag=True, help="Quiet mode - minimal output")
@click.version_option(version=__version__, prog_name="SpotyBot")
@click.pass_context
def cli(ctx, config, output, format, quality, async_downloads, max_concurrent, verbose, quiet):
    """
    🎵 SpotyBot - Spotify Playlist Downloader
    
    Download entire Spotify playlists, albums, or individual tracks using spotDL.
    
    Examples:
      spotybot https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
      spotybot download --format flac --quality 320k <playlist_url>
      spotybot search "The Beatles Hey Jude"
      spotybot interactive
    """
    
    # Store context for subcommands
    ctx.ensure_object(dict)
    
    # Load configuration
    try:
        bot_config = Config.from_env(config)
        
        # Override with CLI options
        if output:
            bot_config.output_directory = Path(output)
        if format:
            bot_config.download_format = format
        if quality:
            bot_config.download_quality = quality
        if max_concurrent:
            bot_config.max_concurrent_downloads = max_concurrent
        if verbose:
            bot_config.log_level = "DEBUG"
        if quiet:
            bot_config.log_level = "ERROR"
            bot_config.show_progress = False
        
        ctx.obj["config"] = bot_config
        ctx.obj["use_async"] = async_downloads
        
    except Exception as e:
        console.print(f"[bold red]❌ Configuration error: {e}[/bold red]")
        sys.exit(1)
    
    # If no subcommand is provided, try to process the first argument as a URL
    if ctx.invoked_subcommand is None:
        args = ctx.params.get("args", [])
        if len(sys.argv) > 1:
            # Get the last argument that's not an option
            url_arg = None
            for arg in sys.argv[1:]:
                if not arg.startswith("-") and "spotify.com" in arg:
                    url_arg = arg
                    break
            
            if url_arg:
                # Process as URL
                try:
                    bot = SpotyBot(config=ctx.obj["config"])
                    url_type, is_valid = bot.validate_url(url_arg)
                    
                    if is_valid:
                        console.print(f"[bold cyan]🎵 Processing {url_type}: {url_arg}[/bold cyan]")
                        
                        if url_type == "playlist":
                            success = bot.download_playlist(url_arg, use_async=ctx.obj["use_async"])
                        elif url_type == "album":
                            success = bot.download_album(url_arg, use_async=ctx.obj["use_async"])
                        elif url_type == "track":
                            success = bot.download_track(url_arg)
                        
                        sys.exit(0 if success else 1)
                    else:
                        console.print(f"[bold red]❌ Invalid Spotify URL: {url_arg}[/bold red]")
                        sys.exit(1)
                        
                except Exception as e:
                    console.print(f"[bold red]❌ Error: {e}[/bold red]")
                    sys.exit(1)
            else:
                # No URL found, show help
                console.print(ctx.get_help())


@cli.command()
@click.argument("url")
@click.option("--max-tracks", "-n", type=int, help="Maximum number of tracks to download")
@click.option("--info-only", is_flag=True, help="Show playlist info without downloading")
@click.pass_context
def playlist(ctx, url, max_tracks, info_only):
    """Download a Spotify playlist
    
    Tracks will be organized in a subfolder named after the playlist
    inside your configured output directory.
    """
    try:
        bot = SpotyBot(config=ctx.obj["config"])
        
        if info_only:
            info = bot.get_playlist_info(url)
            console.print(f"[bold green]📋 Playlist: {info['name']}[/bold green]")
            console.print(f"👤 Owner: {info['owner']}")
            console.print(f"🎵 Total tracks: {info['total_tracks']}")
            console.print(f"🔗 URL: {info['url']}")
            if info.get('description'):
                console.print(f"📝 Description: {info['description']}")
        else:
            success = bot.download_playlist(
                url, 
                max_tracks=max_tracks, 
                use_async=ctx.obj["use_async"]
            )
            sys.exit(0 if success else 1)
            
    except Exception as e:
        console.print(f"[bold red]❌ Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.argument("url")
@click.pass_context
def album(ctx, url):
    """Download a Spotify album
    
    Tracks will be organized in a subfolder named after the album
    inside your configured output directory.
    """
    try:
        bot = SpotyBot(config=ctx.obj["config"])
        success = bot.download_album(url, use_async=ctx.obj["use_async"])
        sys.exit(0 if success else 1)
        
    except Exception as e:
        console.print(f"[bold red]❌ Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.argument("url")
@click.pass_context
def track(ctx, url):
    """Download a single Spotify track"""
    try:
        bot = SpotyBot(config=ctx.obj["config"])
        success = bot.download_track(url)
        sys.exit(0 if success else 1)
        
    except Exception as e:
        console.print(f"[bold red]❌ Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.argument("query")
@click.option("--limit", "-l", type=int, default=1, help="Number of tracks to download")
@click.pass_context
def search(ctx, query, limit):
    """Search for and download tracks"""
    try:
        bot = SpotyBot(config=ctx.obj["config"])
        success = bot.search_and_download(query, limit=limit)
        sys.exit(0 if success else 1)
        
    except Exception as e:
        console.print(f"[bold red]❌ Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.argument("url")
@click.option("--max-tracks", "-n", type=int, help="Maximum number of tracks to download")
@click.pass_context
def download(ctx, url, max_tracks):
    """Download from any Spotify URL (auto-detect type)"""
    try:
        bot = SpotyBot(config=ctx.obj["config"])
        url_type, is_valid = bot.validate_url(url)
        
        if not is_valid:
            console.print(f"[bold red]❌ Invalid Spotify URL: {url}[/bold red]")
            sys.exit(1)
        
        console.print(f"[bold cyan]🎵 Processing {url_type}: {url}[/bold cyan]")
        
        if url_type == "playlist":
            success = bot.download_playlist(url, max_tracks=max_tracks, use_async=ctx.obj["use_async"])
        elif url_type == "album":
            success = bot.download_album(url, use_async=ctx.obj["use_async"])
        elif url_type == "track":
            success = bot.download_track(url)
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        console.print(f"[bold red]❌ Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def interactive(ctx):
    """Run SpotyBot in interactive mode"""
    try:
        bot = SpotyBot(config=ctx.obj["config"])
        bot.run_interactive()
        
    except KeyboardInterrupt:
        console.print("\n[bold green]👋 Goodbye![/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def config_info(ctx):
    """Show current configuration"""
    try:
        bot = SpotyBot(config=ctx.obj["config"])
        bot.print_config_summary()
        
    except Exception as e:
        console.print(f"[bold red]❌ Error: {e}[/bold red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def setup(ctx):
    """Interactive setup wizard"""
    console.print("[bold cyan]🔧 SpotyBot Setup Wizard[/bold cyan]")
    console.print("\nThis wizard will help you configure SpotyBot.")
    console.print("You'll need Spotify API credentials from: https://developer.spotify.com/dashboard\n")
    
    # Check if .env already exists
    env_file = Path(".env")
    if env_file.exists():
        if not click.confirm("Found existing .env file. Overwrite?"):
            console.print("[yellow]Setup cancelled.[/yellow]")
            return
    
    try:
        # Get Spotify credentials
        console.print("[bold green]1. Spotify API Credentials[/bold green]")
        client_id = click.prompt("Enter your Spotify Client ID")
        client_secret = click.prompt("Enter your Spotify Client Secret", hide_input=True)
        
        # Get download preferences
        console.print("\n[bold green]2. Download Preferences[/bold green]")
        output_dir = click.prompt("Output directory", default="./downloads")
        format_choice = click.prompt(
            "Audio format", 
            type=click.Choice(["mp3", "flac", "ogg", "opus", "m4a"]), 
            default="mp3"
        )
        quality = click.prompt(
            "Audio quality", 
            type=click.Choice(["96k", "128k", "160k", "192k", "256k", "320k"]), 
            default="320k"
        )
        
        # Write .env file
        env_content = f"""# Spotify API Configuration
SPOTIFY_CLIENT_ID={client_id}
SPOTIFY_CLIENT_SECRET={client_secret}

# Download Configuration
DOWNLOAD_FORMAT={format_choice}
DOWNLOAD_QUALITY={quality}
OUTPUT_DIRECTORY={output_dir}

# Download Behavior
MAX_CONCURRENT_DOWNLOADS=4
SKIP_EXISTING_FILES=true
EMBED_METADATA=true
DOWNLOAD_LYRICS=true

# Audio Provider
AUDIO_PROVIDER=youtube-music
"""
        
        with open(".env", "w") as f:
            f.write(env_content)
        
        console.print("\n[bold green]✅ Configuration saved to .env[/bold green]")
        console.print("You can now use SpotyBot! Try: spotybot interactive")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]❌ Setup error: {e}[/bold red]")


def main():
    """Main entry point"""
    try:
        cli()
    except Exception as e:
        console.print(f"[bold red]❌ Fatal error: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()