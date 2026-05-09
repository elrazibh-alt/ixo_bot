"""
Instagram downloader — supports Reels, Posts, Carousels, Stories.
Uses yt-dlp; cookies are optional but improve story/highlight access.
"""

import asyncio
import logging
from pathlib import Path

import yt_dlp

from core.base_downloader import BaseDownloader, MediaInfo

logger = logging.getLogger(__name__)


class InstagramDownloader(BaseDownloader):
    supported_domains = ["instagram.com", "instagr.am"]

    async def download(self, url: str, quality: str,
                       download_dir: Path) -> MediaInfo:
        out_path = self._unique_path(download_dir, "mp4")
        opts = self._build_ydl_opts(out_path, quality)

        # Instagram-specific tweaks
        opts.update({
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                    "Version/17.0 Mobile/15E148 Safari/604.1"
                ),
                "Referer": "https://www.instagram.com/",
            },
        })

        def _run():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info

        info_dict = await asyncio.to_thread(_run)

        # Handle playlist (carousel)
        if info_dict.get("_type") == "playlist":
            entries = info_dict.get("entries", [])
            if entries:
                info_dict = entries[0]

        # Find the actual file (yt-dlp may add extension suffix)
        actual = _resolve_path(out_path)
        size = actual.stat().st_size if actual else 0

        return MediaInfo(
            title=info_dict.get("title", "Instagram post"),
            description=info_dict.get("description", ""),
            uploader=info_dict.get("uploader", ""),
            duration=info_dict.get("duration"),
            view_count=info_dict.get("view_count"),
            upload_date=info_dict.get("upload_date"),
            thumbnail_url=info_dict.get("thumbnail"),
            direct_url=info_dict.get("url"),
            file_path=actual,
            file_size=size,
            media_type="video",
            hashtags=self._extract_hashtags(info_dict.get("description", "")),
        )


def _resolve_path(base: Path) -> Path:
    """yt-dlp appends extension; find whatever file matches the stem."""
    if base.exists():
        return base
    parent = base.parent
    stem = base.stem
    for candidate in parent.glob(f"{stem}*"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Downloaded file not found near {base}")
