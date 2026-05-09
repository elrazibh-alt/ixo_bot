"""YouTube downloader — video and audio, respects quality param."""

import asyncio
import logging
from pathlib import Path

import yt_dlp

from core.base_downloader import BaseDownloader, MediaInfo
from downloaders.instagram import _resolve_path

logger = logging.getLogger(__name__)


class YouTubeDownloader(BaseDownloader):
    supported_domains = ["youtube.com", "youtu.be"]

    async def download(self, url: str, quality: str,
                       download_dir: Path) -> MediaInfo:
        is_audio = quality == "audio"
        ext = "mp3" if is_audio else "mp4"
        out_path = self._unique_path(download_dir, ext)
        opts = self._build_ydl_opts(out_path, quality)

        if is_audio:
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
            opts["format"] = "bestaudio/best"

        def _run():
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=True)

        info_dict = await asyncio.to_thread(_run)
        actual = _resolve_path(out_path)

        return MediaInfo(
            title=info_dict.get("title", "YouTube video"),
            description=info_dict.get("description", ""),
            uploader=info_dict.get("uploader", ""),
            duration=info_dict.get("duration"),
            view_count=info_dict.get("view_count"),
            upload_date=info_dict.get("upload_date"),
            thumbnail_url=info_dict.get("thumbnail"),
            file_path=actual,
            file_size=actual.stat().st_size,
            media_type="audio" if is_audio else "video",
        )
