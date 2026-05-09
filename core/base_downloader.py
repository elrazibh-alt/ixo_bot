"""
Abstract base class for all platform downloaders.
Each concrete downloader only needs to implement `download()`.
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class MediaInfo:
    """Metadata extracted alongside the file."""
    title: str = ""
    description: str = ""
    uploader: str = ""
    duration: Optional[int] = None          # seconds
    view_count: Optional[int] = None
    upload_date: Optional[str] = None       # YYYYMMDD
    thumbnail_url: Optional[str] = None
    direct_url: Optional[str] = None
    file_path: Optional[Path] = None
    file_size: int = 0
    platform: str = ""
    media_type: str = "video"              # video | audio | image
    hashtags: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    @property
    def size_mb(self) -> float:
        return self.file_size / (1024 * 1024)

    @property
    def duration_str(self) -> str:
        if not self.duration:
            return "N/A"
        m, s = divmod(self.duration, 60)
        return f"{m:02d}:{s:02d}"


class BaseDownloader(ABC):
    """
    Template for all platform downloaders.

    Subclasses must implement:
        download(url, quality, download_dir) -> MediaInfo

    Subclasses may override:
        supported_domains  — used by the router for lookup
        _build_ydl_opts()  — if they use yt-dlp
    """

    #: Override in subclass with your platform's domains
    supported_domains: list[str] = []

    def __init__(self, timeout: int = 120, retries: int = 3,
                 cookies_file: Optional[str] = None):
        self.timeout = timeout
        self.retries = retries
        self.cookies_file = cookies_file
        self._semaphore: Optional[asyncio.Semaphore] = None

    def set_semaphore(self, sem: asyncio.Semaphore) -> None:
        """Attach a shared concurrency semaphore from the download manager."""
        self._semaphore = sem

    # ── Public API ────────────────────────────────────────────────────────────

    async def safe_download(self, url: str, quality: str = "best",
                            download_dir: Path = Path("downloads")) -> MediaInfo:
        """Retry wrapper around download()."""
        last_exc: Optional[Exception] = None
        for attempt in range(1, self.retries + 1):
            try:
                if self._semaphore:
                    async with self._semaphore:
                        return await self.download(url, quality, download_dir)
                return await self.download(url, quality, download_dir)
            except Exception as exc:
                last_exc = exc
                logger.warning("[%s] attempt %d/%d failed: %s",
                               self.__class__.__name__, attempt, self.retries, exc)
                if attempt < self.retries:
                    await asyncio.sleep(2 ** attempt)   # exponential back-off
        raise RuntimeError(
            f"All {self.retries} download attempts failed. Last error: {last_exc}"
        ) from last_exc

    @abstractmethod
    async def download(self, url: str, quality: str,
                       download_dir: Path) -> MediaInfo:
        """Platform-specific download logic. Must return a populated MediaInfo."""

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _unique_path(self, directory: Path, extension: str = "mp4") -> Path:
        """Generate a collision-free file path."""
        return directory / f"{uuid.uuid4().hex[:12]}.{extension}"

    def _build_ydl_opts(self, out_path: Path, quality: str = "best",
                        extra: Optional[dict] = None) -> dict:
        """
        Sensible yt-dlp defaults.
        Subclasses can call super()._build_ydl_opts() then mutate the result.
        """
        fmt = self._quality_to_format(quality)
        opts: dict = {
            "quiet": True,
            "no_warnings": True,
            "outtmpl": str(out_path),
            "format": fmt,
            "retries": self.retries,
            "socket_timeout": self.timeout,
            "merge_output_format": "mp4",
            "postprocessors": [{"key": "FFmpegVideoConvertor",
                                "preferedformat": "mp4"}],
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        if self.cookies_file:
            opts["cookiefile"] = self.cookies_file
        if extra:
            opts.update(extra)
        return opts

    @staticmethod
    def _quality_to_format(quality: str) -> str:
        mapping = {
            "best":   "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "1080p":  "bestvideo[height<=1080][ext=mp4]+bestaudio/best[height<=1080]",
            "720p":   "bestvideo[height<=720][ext=mp4]+bestaudio/best[height<=720]",
            "480p":   "bestvideo[height<=480][ext=mp4]+bestaudio/best[height<=480]",
            "audio":  "bestaudio[ext=m4a]/bestaudio",
        }
        return mapping.get(quality, mapping["best"])

    @staticmethod
    def _extract_hashtags(text: Optional[str]) -> list[str]:
        if not text:
            return []
        return re.findall(r"#\w+", text)


# Avoid circular import: import re at top level only if needed
import re  # noqa: E402 — intentionally placed after class body
