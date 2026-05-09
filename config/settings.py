"""
Central configuration module — reads from environment variables with fallbacks.
All secrets MUST be set via .env or platform environment vars.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent


@dataclass
class BotConfig:
    # ── Telegram ──────────────────────────────────────────────────────────────
    TOKEN: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    WEBHOOK_URL: str = field(default_factory=lambda: os.getenv("WEBHOOK_URL", ""))
    WEBHOOK_PORT: int = field(default_factory=lambda: int(os.getenv("WEBHOOK_PORT", "8443")))
    USE_WEBHOOK: bool = field(default_factory=lambda: bool(os.getenv("WEBHOOK_URL")))

    # ── Paths ─────────────────────────────────────────────────────────────────
    BASE_DIR: Path = BASE_DIR
    DOWNLOAD_DIR: Path = BASE_DIR / "downloads"
    CACHE_DIR: Path = BASE_DIR / "cache"
    LOG_DIR: Path = BASE_DIR / "logs"

    # ── Limits ────────────────────────────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = field(default_factory=lambda: int(os.getenv("MAX_FILE_SIZE_MB", "50")))
    MAX_CONCURRENT_DOWNLOADS: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT", "5")))
    DOWNLOAD_TIMEOUT: int = field(default_factory=lambda: int(os.getenv("DOWNLOAD_TIMEOUT", "120")))
    RETRY_COUNT: int = field(default_factory=lambda: int(os.getenv("RETRY_COUNT", "3")))

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_CALLS: int = 5          # max requests per window
    RATE_LIMIT_PERIOD: int = 60        # seconds

    # ── Optional cookies / credentials ───────────────────────────────────────
    INSTAGRAM_COOKIES: str = field(default_factory=lambda: os.getenv("INSTAGRAM_COOKIES", ""))
    YOUTUBE_COOKIES: str = field(default_factory=lambda: os.getenv("YOUTUBE_COOKIES", ""))

    # ── Redis (optional) ──────────────────────────────────────────────────────
    REDIS_URL: str = field(default_factory=lambda: os.getenv("REDIS_URL", ""))

    # ── Health-check server ───────────────────────────────────────────────────
    # PORT is injected by Render / Railway automatically; default 8080 locally.
    HEALTH_PORT: int = field(default_factory=lambda: int(os.getenv("PORT", "8080")))
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    DEBUG: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    def __post_init__(self):
        """Create required directories on startup."""
        for d in (self.DOWNLOAD_DIR, self.CACHE_DIR, self.LOG_DIR):
            d.mkdir(parents=True, exist_ok=True)

    @property
    def MAX_FILE_SIZE(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


# Singleton — import this everywhere
settings = BotConfig()
