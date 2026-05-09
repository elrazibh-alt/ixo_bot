"""TikTok downloader — removes watermark via yt-dlp format selection."""

import asyncio
import logging
from pathlib import Path

import yt_dlp

from core.base_downloader import BaseDownloader, MediaInfo
from downloaders.instagram import _resolve_path

logger = logging.getLogger(__name__)


class TikTokDownloader(BaseDownloader):
    supported_domains = ["tiktok.com", "vm.tiktok.com", "vt.tiktok.com"]

    async def download(self, url: str, quality: str,
                       download_dir: Path) -> MediaInfo:
        out_path = self._unique_path(download_dir, "mp4")
        opts = self._build_ydl_opts(out_path, quality)

        # Prefer no-watermark format when available
        opts["format"] = (
            "download_addr-0/play_addr-0/"
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        )
        opts["http_headers"] = {
            "User-Agent": (
                "com.zhiliaoapp.musically/2022600030 "
                "(Linux; U; Android 10; en_US; Pixel 4; "
                "Build/QQ3A.200805.001; tt-ok/3.12.13.1)"
            ),
            "Referer": "https://www.tiktok.com/",
        }

        def _run():
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=True)

        info_dict = await asyncio.to_thread(_run)
        actual = _resolve_path(out_path)

        return MediaInfo(
            title=info_dict.get("title", "TikTok video"),
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
