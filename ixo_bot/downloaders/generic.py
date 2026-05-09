"""
Generic yt-dlp downloader — used for Facebook, Reddit, Pinterest,
Vimeo, SoundCloud, Threads, Dailymotion, and any unknown platform.
Individual wrappers simply sub-class and set supported_domains.
"""

import asyncio
import logging
from pathlib import Path

import yt_dlp

from core.base_downloader import BaseDownloader, MediaInfo
from downloaders.instagram import _resolve_path

logger = logging.getLogger(__name__)


class GenericDownloader(BaseDownloader):
    """Fallback for any URL yt-dlp supports."""
    supported_domains: list[str] = []

    async def download(self, url: str, quality: str,
                       download_dir: Path) -> MediaInfo:
        out_path = self._unique_path(download_dir, "mp4")
        opts = self._build_ydl_opts(out_path, quality)

        def _run():
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=True)

        info_dict = await asyncio.to_thread(_run)
        actual = _resolve_path(out_path)

        return MediaInfo(
            title=info_dict.get("title", "Media"),
            description=info_dict.get("description", ""),
            uploader=info_dict.get("uploader", ""),
            duration=info_dict.get("duration"),
            view_count=info_dict.get("view_count"),
            upload_date=info_dict.get("upload_date"),
            thumbnail_url=info_dict.get("thumbnail"),
            file_path=actual,
            file_size=actual.stat().st_size,
            media_type="video",
            hashtags=self._extract_hashtags(info_dict.get("description", "")),
        )


# ── Per-platform thin wrappers ────────────────────────────────────────────────

class FacebookDownloader(GenericDownloader):
    supported_domains = ["facebook.com", "fb.watch", "m.facebook.com"]


class RedditDownloader(GenericDownloader):
    supported_domains = ["reddit.com", "redd.it"]


class PinterestDownloader(GenericDownloader):
    supported_domains = ["pinterest.com", "pin.it"]


class VimeoDownloader(GenericDownloader):
    supported_domains = ["vimeo.com"]


class SoundCloudDownloader(GenericDownloader):
    supported_domains = ["soundcloud.com"]

    async def download(self, url: str, quality: str,
                       download_dir: Path) -> MediaInfo:
        # Force audio output for SoundCloud
        out_path = self._unique_path(download_dir, "mp3")
        opts = self._build_ydl_opts(out_path, "audio")
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        }]

        def _run():
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=True)

        info_dict = await asyncio.to_thread(_run)
        actual = _resolve_path(out_path)

        return MediaInfo(
            title=info_dict.get("title", "SoundCloud track"),
            description=info_dict.get("description", ""),
            uploader=info_dict.get("uploader", ""),
            duration=info_dict.get("duration"),
            view_count=info_dict.get("view_count"),
            upload_date=info_dict.get("upload_date"),
            thumbnail_url=info_dict.get("thumbnail"),
            file_path=actual,
            file_size=actual.stat().st_size,
            media_type="audio",
        )


class ThreadsDownloader(GenericDownloader):
    supported_domains = ["threads.net"]


class DailymotionDownloader(GenericDownloader):
    supported_domains = ["dailymotion.com"]
