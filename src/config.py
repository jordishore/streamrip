"""A config class that manages arguments between the config file and CLI."""

import copy
import logging
import os
from dataclasses import dataclass

from tomlkit.api import dumps, parse
from tomlkit.toml_document import TOMLDocument

logger = logging.getLogger("streamrip")

CURRENT_CONFIG_VERSION = "2.0"

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.toml")


@dataclass(slots=True)
class QobuzConfig:
    use_auth_token: bool
    email_or_userid: str
    # This is an md5 hash of the plaintext password
    password_or_token: str
    # Do not change
    app_id: str
    quality: int
    # This will download booklet pdfs that are included with some albums
    download_booklets: bool
    # Do not change
    secrets: list[str]


@dataclass(slots=True)
class TidalConfig:
    # Do not change any of the fields below
    user_id: str
    country_code: str
    access_token: str
    refresh_token: str
    # Tokens last 1 week after refresh. This is the Unix timestamp of the expiration
    # time. If you haven't used streamrip in more than a week, you may have to log
    # in again using `rip config --tidal`
    token_expiry: str
    # 0: 256kbps AAC, 1: 320kbps AAC, 2: 16/44.1 "HiFi" FLAC, 3: 24/44.1 "MQA" FLAC
    quality: int
    # This will download videos included in Video Albums.
    download_videos: bool


@dataclass(slots=True)
class DeezerConfig:
    # An authentication cookie that allows streamrip to use your Deezer account
    # See https://github.com/nathom/streamrip/wiki/Finding-Your-Deezer-ARL-Cookie
    # for instructions on how to find this
    arl: str
    # 0, 1, or 2
    # This only applies to paid Deezer subscriptions. Those using deezloader
    # are automatically limited to quality = 1
    quality: int
    # This allows for free 320kbps MP3 downloads from Deezer
    # If an arl is provided, deezloader is never used
    use_deezloader: bool
    # This warns you when the paid deezer account is not logged in and rip falls
    # back to deezloader, which is unreliable
    deezloader_warnings: bool


@dataclass(slots=True)
class SoundcloudConfig:
    # This changes periodically, so it needs to be updated
    client_id: str
    app_version: str
    # Only 0 is available for now
    quality: int


@dataclass(slots=True)
class YoutubeConfig:
    # The path to download the videos to
    video_downloads_folder: str
    # Only 0 is available for now
    quality: int
    # Download the video along with the audio
    download_videos: bool


@dataclass(slots=True)
class DatabaseConfig:
    downloads_enabled: bool
    downloads_path: str
    failed_downloads_enabled: bool
    failed_downloads_path: str


@dataclass(slots=True)
class ConversionConfig:
    enabled: bool
    # FLAC, ALAC, OPUS, MP3, VORBIS, or AAC
    codec: str
    # In Hz. Tracks are downsampled if their sampling rate is greater than this.
    # Value of 48000 is recommended to maximize quality and minimize space
    sampling_rate: int
    # Only 16 and 24 are available. It is only applied when the bit depth is higher
    # than this value.
    bit_depth: int
    # Only applicable for lossy codecs
    lossy_bitrate: int


@dataclass(slots=True)
class QobuzDiscographyFilterConfig:
    # Remove Collectors Editions, live recordings, etc.
    extras: bool
    # Picks the highest quality out of albums with identical titles.
    repeats: bool
    # Remove EPs and Singles
    non_albums: bool
    # Remove albums whose artist is not the one requested
    features: bool
    # Skip non studio albums
    non_studio_albums: bool
    # Only download remastered albums
    non_remaster: bool


@dataclass(slots=True)
class ArtworkConfig:
    # Write the image to the audio file
    embed: bool
    # The size of the artwork to embed. Options: thumbnail, small, large, original.
    # "original" images can be up to 30MB, and may fail embedding.
    # Using "large" is recommended.
    size: str
    # Both of these options limit the size of the embedded artwork. If their values
    # are larger than the actual dimensions of the image, they will be ignored.
    # If either value is -1, the image is left untouched.
    max_width: int
    max_height: int
    # Save the cover image at the highest quality as a seperate jpg file
    keep_hires_cover: bool


@dataclass(slots=True)
class MetadataConfig:
    # Sets the value of the 'ALBUM' field in the metadata to the playlist's name.
    # This is useful if your music library software organizes tracks based on album name.
    set_playlist_to_album: bool
    # Replaces the original track's tracknumber with it's position in the playlist
    new_playlist_tracknumbers: bool
    # The following metadata tags won't be applied
    # See https://github.com/nathom/streamrip/wiki/Metadata-Tag-Names for more info
    exclude: list[str]


@dataclass(slots=True)
class FilepathsConfig:
    # Create folders for single tracks within the downloads directory using the folder_format
    # template
    add_singles_to_folder: bool
    # Available keys: "albumartist", "title", "year", "bit_depth", "sampling_rate",
    # "container", "id", and "albumcomposer"
    folder_format: str
    # Available keys: "tracknumber", "artist", "albumartist", "composer", "title",
    # and "albumcomposer"
    track_format: str
    # Only allow printable ASCII characters in filenames.
    restrict_characters: bool
    # Truncate the filename if it is greater than 120 characters
    # Setting this to false may cause downloads to fail on some systems
    truncate: bool


@dataclass(slots=True)
class DownloadsConfig:
    # Folder where tracks are downloaded to
    folder: str
    # Put Qobuz albums in a 'Qobuz' folder, Tidal albums in 'Tidal' etc.
    source_subdirectories: bool
    # Download (and convert) tracks all at once, instead of sequentially.
    # If you are converting the tracks, or have fast internet, this will
    # substantially improve processing speed.
    concurrency: bool
    # The maximum number of tracks to download at once
    # If you have very fast internet, you will benefit from a higher value,
    # A value that is too high for your bandwidth may cause slowdowns
    max_connections: int
    requests_per_minute: int


@dataclass(slots=True)
class LastFmConfig:
    # The source on which to search for the tracks.
    source: str
    # If no results were found with the primary source, the item is searched for
    # on this one.
    fallback_source: str


@dataclass(slots=True)
class ThemeConfig:
    # Options: "dainty" or "plain"
    progress_bar: str


@dataclass(slots=True)
class ConfigData:
    toml: TOMLDocument
    downloads: DownloadsConfig

    qobuz: QobuzConfig
    tidal: TidalConfig
    deezer: DeezerConfig
    soundcloud: SoundcloudConfig
    youtube: YoutubeConfig
    lastfm: LastFmConfig

    filepaths: FilepathsConfig
    artwork: ArtworkConfig
    metadata: MetadataConfig
    qobuz_filter: QobuzDiscographyFilterConfig

    theme: ThemeConfig
    database: DatabaseConfig

    _modified: bool = False

    @classmethod
    def from_toml(cls, toml_str: str):
        # TODO: handle the mistake where Windows people forget to escape backslash
        toml = parse(toml_str)
        if toml["misc"]["version"] != CURRENT_CONFIG_VERSION:  # type: ignore
            raise Exception("Need to update config")

        downloads = DownloadsConfig(**toml["downloads"])  # type: ignore
        qobuz = QobuzConfig(**toml["qobuz"])  # type: ignore
        tidal = TidalConfig(**toml["tidal"])  # type: ignore
        deezer = DeezerConfig(**toml["deezer"])  # type: ignore
        soundcloud = SoundcloudConfig(**toml["soundcloud"])  # type: ignore
        youtube = YoutubeConfig(**toml["youtube"])  # type: ignore
        lastfm = LastFmConfig(**toml["lastfm"])  # type: ignore
        artwork = ArtworkConfig(**toml["artwork"])  # type: ignore
        filepaths = FilepathsConfig(**toml["filepaths"])  # type: ignore
        metadata = MetadataConfig(**toml["metadata"])  # type: ignore
        qobuz_filter = QobuzDiscographyFilterConfig(**toml["qobuz_filters"])  # type: ignore
        theme = ThemeConfig(**toml["theme"])  # type: ignore
        database = DatabaseConfig(**toml["database"])  # type: ignore

        return cls(
            toml=toml,
            downloads=downloads,
            qobuz=qobuz,
            tidal=tidal,
            deezer=deezer,
            soundcloud=soundcloud,
            youtube=youtube,
            lastfm=lastfm,
            artwork=artwork,
            filepaths=filepaths,
            metadata=metadata,
            qobuz_filter=qobuz_filter,
            theme=theme,
            database=database,
        )

    @classmethod
    def defaults(cls):
        with open(DEFAULT_CONFIG_PATH) as f:
            return cls.from_toml(f.read())

    def set_modified(self):
        self._modified = True

    @property
    def modified(self):
        return self._modified

    def update_toml(self):
        pass


class Config:
    def __init__(self, path: str):
        self._path = path

        with open(path) as toml_file:
            self.file: ConfigData = ConfigData.from_toml(toml_file.read())

        self.session: ConfigData = copy.deepcopy(self.file)

    def save_file(self):
        if not self.file.modified:
            return

        with open(self._path, "w") as toml_file:
            self.file.update_toml()
            toml_file.write(dumps(self.file.toml))