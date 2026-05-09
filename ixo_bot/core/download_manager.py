"""
Download Manager — central dispatcher.

Usage:
    manager = DownloadManager(settings)
    info = await manager.download(url, quality)
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from config.settings import BotConfig
from core.base_downloader import BaseDownloader, MediaInfo
from utils.url_parser import Platform, ParsedURL

logger = logging.getLogger(__name__)


class DownloadManager:
    def __init__(self, settings: BotConfig):
        self.settings = settings
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_DOWNLOADS)
        self._downloaders: dict[Platform, BaseDownloader] = {}
        self._register_downloaders()

    # ── Registration ──────────────────────────────────────────────────────────

    def _register_downloaders(self) -> None:
        """Import and register every platform downloader."""
        from downloaders.instagram   import InstagramDownloader
        from downloaders.tiktok      import TikTokDownloader
        from downloaders.youtube     import YouTubeDownloader
        from downloaders.twitter     import TwitterDownloader
        from downloaders.facebook    import FacebookDownloader
        from downloaders.reddit      import RedditDownloader
        from downloaders.pinterest   import PinterestDownloader
        from downloaders.vimeo       import VimeoDownloader
        from downloaders.soundcloud  import SoundCloudDownloader
        from downloaders.threads     import ThreadsDownloader
        from downloaders.dailymotion import DailymotionDownloader
        from downloaders.generic     import GenericDownloader

        pairs: list[tuple[Platform, BaseDownloader]] = [
            (Platform.INSTAGRAM,   InstagramDownloader(
                timeout=self.settings.DOWNLOAD_TIMEOUT,
                retries=self.settings.RETRY_COUNT,
                cookies_file=self.settings.INSTAGRAM_COOKIES or None,
            )),
            (Platform.TIKTOK,      TikTokDownloader(
                timeout=self.settings.DOWNLOAD_TIMEOUT,
                retries=self.settings.RETRY_COUNT,
            )),
            (Platform.YOUTUBE,     YouTubeDownloader(
                timeout=self.settings.DOWNLOAD_TIMEOUT,
                retries=self.settings.RETRY_COUNT,
                cookies_file=self.settings.YOUTUBE_COOKIES or None,
            )),
            (Platform.TWITTER,     TwitterDownloader(
                timeout=self.settings.DOWNLOAD_TIMEOUT,
                retries=self.settings.RETRY_COUNT,
            )),
            (Platform.FACEBOOK,    FacebookDownloader(
                timeout=self.settings.DOWNLOAD_TIMEOUT,
                retries=self.settings.RETRY_COUNT,
            )),
            (Platform.REDDIT,      RedditDownloader(
                timeout=self.settings.DOWNLOAD_TIMEOUT,
                retries=self.settings.RETRY_COUNT,
            )),
            (Platform.PINTEREST,   PinterestDownloader(
                timeout=self.settings.DOWNLOAD_TIMEOUT,
                retries=self.settings.RETRY_COUNT,
            )),
            (Platform.VIMEO,       VimeoDownloader(
                timeout=self.settings.DOWNLOAD_TIMEOUT,
                retries=self.settings.RETRY_COUNT,
            )),
            (Platform.SOUNDCLOUD,  SoundCloudDownloader(
                timeout=self.settings.DOWNLOAD_TIMEOUT,
                retries=self.settings.RETRY_COUNT,
            )),
            (Platform.THREADS,     ThreadsDownloader(
                timeout=self.settings.DOWNLOAD_TIMEOUT,
                retries=self.settings.RETRY_COUNT,
            )),
            (Platform.DAILYMOTION, DailymotionDownloader(
                timeout=self.settings.DOWNLOAD_TIMEOUT,
                retries=self.settings.RETRY_COUNT,
            )),
        ]

        self._generic = GenericDownloader(
            timeout=self.settings.DOWNLOAD_TIMEOUT,
            retries=self.settings.RETRY_COUNT,
        )

        for platform, dl in pairs:
            dl.set_semaphore(self._semaphore)
            self._downloaders[platform] = dl

        self._generic.set_semaphore(self._semaphore)

    # ── Public API ────────────────────────────────────────────────────────────

    async def download(self, parsed: ParsedURL,
                       quality: str = "best") -> MediaInfo:
        """
        Route a validated URL to the correct downloader and return MediaInfo.
        Falls back to GenericDownloader for UNKNOWN platform.
        """
        dl = self._downloaders.get(parsed.platform, self._generic)
        logger.info("Dispatching to %s for %s", dl.__class__.__name__, parsed.platform)

        info = await dl.safe_download(
            url=parsed.clean,
            quality=quality,
            download_dir=self.settings.DOWNLOAD_DIR,
        )
        info.platform = parsed.platform.value
        return info
