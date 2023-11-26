import asyncio
import logging
import os
import shutil
import subprocess
from functools import wraps

import click
from click_help_colors import HelpColorsGroup  # type: ignore
from rich.logging import RichHandler
from rich.prompt import Confirm
from rich.traceback import install

from ..config import DEFAULT_CONFIG_PATH, Config, set_user_defaults
from ..console import console
from .main import Main
from .user_paths import DEFAULT_CONFIG_PATH


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@click.group(
    cls=HelpColorsGroup,
    help_headers_color="yellow",
    help_options_color="green",
)
@click.version_option(version="2.0")
@click.option(
    "--config-path", default=DEFAULT_CONFIG_PATH, help="Path to the configuration file"
)
@click.option("-f", "--folder", help="The folder to download items into.")
@click.option(
    "-ndb",
    "--no-db",
    help="Download items even if they have been logged in the database",
    default=False,
    is_flag=True,
)
@click.option("-q", "--quality", help="The maximum quality allowed to download")
@click.option(
    "-c",
    "--convert",
    help="Convert the downloaded files to an audio codec (ALAC, FLAC, MP3, AAC, or OGG)",
)
@click.option(
    "--no-progress", help="Do not show progress bars", is_flag=True, default=False
)
@click.option(
    "-v", "--verbose", help="Enable verbose output (debug mode)", is_flag=True
)
@click.pass_context
def rip(ctx, config_path, folder, no_db, quality, convert, no_progress, verbose):
    """
    Streamrip: the all in one music downloader.
    """
    global logger
    logging.basicConfig(
        level="INFO", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
    )
    logger = logging.getLogger("streamrip")
    if verbose:
        install(
            console=console,
            suppress=[click],
            show_locals=True,
            locals_hide_sunder=False,
        )
        logger.setLevel(logging.DEBUG)
        logger.debug("Showing all debug logs")
    else:
        install(console=console, suppress=[click, asyncio], max_frames=1)
        logger.setLevel(logging.WARNING)

    if not os.path.isfile(config_path):
        console.print(
            f"No file found at [bold cyan]{config_path}[/bold cyan], creating default config."
        )
        set_user_defaults(config_path)

    # pass to subcommands
    ctx.ensure_object(dict)

    c = Config(config_path)
    # set session config values to command line args
    c.session.database.downloads_enabled = not no_db
    if folder is not None:
        c.session.downloads.folder = folder

    if quality is not None:
        c.session.qobuz.quality = quality
        c.session.tidal.quality = quality
        c.session.deezer.quality = quality
        c.session.soundcloud.quality = quality

    if convert is not None:
        c.session.conversion.enabled = True
        assert convert.upper() in ("ALAC", "FLAC", "OGG", "MP3", "AAC")
        c.session.conversion.codec = convert.upper()

    if no_progress:
        c.session.cli.progress_bars = False

    ctx.obj["config"] = c


@rip.command()
@click.argument("urls", nargs=-1, required=True)
@click.pass_context
@coro
async def url(ctx, urls):
    """Download content from URLs."""
    with ctx.obj["config"] as cfg:
        async with Main(cfg) as main:
            await main.add_all(urls)
            await main.resolve()
            await main.rip()


@rip.command()
@click.argument("path", required=True)
@click.pass_context
@coro
async def file(ctx, path):
    """Download content from URLs in a file seperated by newlines.

    Example usage:

        rip file urls.txt
    """
    with ctx.obj["config"] as cfg:
        async with Main(cfg) as main:
            with open(path) as f:
                await main.add_all([line for line in f])
            await main.resolve()
            await main.rip()


@rip.group()
def config():
    """Manage configuration files."""
    pass


@config.command("open")
@click.option("-v", "--vim", help="Open in (Neo)Vim", is_flag=True)
@click.pass_context
def config_open(ctx, vim):
    """Open the config file in a text editor."""
    config_path = ctx.obj["config"].path
    console.log(f"Opening file at [bold cyan]{config_path}")
    if vim:
        if shutil.which("nvim") is not None:
            subprocess.run(["nvim", config_path])
        else:
            subprocess.run(["vim", config_path])
    else:
        click.launch(config_path)


@config.command("reset")
@click.option("-y", "--yes", help="Don't ask for confirmation.", is_flag=True)
@click.pass_context
def config_reset(ctx, yes):
    """Reset the config file."""
    config_path = ctx.obj["config"].path
    if not yes:
        if not Confirm.ask(
            f"Are you sure you want to reset the config file at {config_path}?"
        ):
            console.print("[green]Reset aborted")
            return

    set_user_defaults(config_path)
    console.print(f"Reset the config file at [bold cyan]{config_path}!")


@rip.command()
@click.option(
    "-f",
    "--first",
    help="Automatically download the first search result without showing the menu.",
    is_flag=True,
)
@click.argument("source", required=True)
@click.argument("media-type", required=True)
@click.argument("query", required=True)
@click.pass_context
@coro
async def search(ctx, first, source, media_type, query):
    """
    Search for content using a specific source.

    Example:

        rip search qobuz album 'rumours'
    """
    with ctx.obj["config"] as cfg:
        async with Main(cfg) as main:
            if first:
                await main.search_take_first(source, media_type, query)
            else:
                await main.search_interactive(source, media_type, query)
            await main.resolve()
            await main.rip()


@rip.command()
@click.argument("url", required=True)
def lastfm(url):
    """Download tracks from a last.fm playlist using a supported source."""
    raise NotImplementedError


if __name__ == "__main__":
    rip()
