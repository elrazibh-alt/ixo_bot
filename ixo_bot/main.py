#!/usr/bin/env python3
"""
IXO Multi-Platform Downloader Bot — entry point.

Run locally:
    python main.py

Render / Railway / Koyeb / VPS:
    Set BOT_TOKEN (required) and PORT (optional, default 8080) in environment.
    The bot always runs in polling mode.
    A lightweight Flask health-check server runs on PORT in a background thread
    so the cloud platform's health pings receive 200 OK responses.
"""

import asyncio
import logging
import os
import sys
import threading

from flask import Flask
from telegram.ext import Application

from bot.handlers import init_handlers, register
from config.settings import settings
from core.download_manager import DownloadManager
from utils.cleanup import periodic_cleanup
from utils.logger import setup_logging
from utils.rate_limiter import RateLimiter

setup_logging(settings.LOG_DIR, settings.LOG_LEVEL, settings.DEBUG)
logger = logging.getLogger(__name__)

# ── Health-check server ───────────────────────────────────────────────────────

_flask_app = Flask(__name__)


@_flask_app.get("/")
@_flask_app.get("/health")
def health():
    """Simple liveness endpoint — returns 200 OK with a JSON body."""
    return {"status": "ok", "bot": "IXO Downloader"}, 200


def _start_health_server() -> None:
    """Run Flask in its own daemon thread (non-blocking relative to asyncio loop)."""
    port = int(os.getenv("PORT", "8080"))
    logger.info("Health-check server starting on 0.0.0.0:%d", port)
    # use_reloader=False is mandatory inside a thread
    _flask_app.run(host="0.0.0.0", port=port, use_reloader=False, threaded=True)


# ── Bot startup ───────────────────────────────────────────────────────────────

async def main() -> None:
    # ── Validate required config ──────────────────────────────────────────────
    if not settings.TOKEN:
        logger.critical("BOT_TOKEN is not set. Exiting.")
        sys.exit(1)

    # ── Start health-check server in background thread ────────────────────────
    health_thread = threading.Thread(target=_start_health_server, daemon=True)
    health_thread.start()

    # ── Build shared services ─────────────────────────────────────────────────
    manager = DownloadManager(settings)
    limiter = RateLimiter(
        max_calls=settings.RATE_LIMIT_CALLS,
        period=settings.RATE_LIMIT_PERIOD,
    )

    # ── Wire handlers ─────────────────────────────────────────────────────────
    init_handlers(settings, manager, limiter)

    # ── Build Telegram application ────────────────────────────────────────────
    app = Application.builder().token(settings.TOKEN).build()
    register(app)

    # ── Background task — periodic download cleanup ───────────────────────────
    asyncio.get_event_loop().create_task(
        periodic_cleanup(settings.DOWNLOAD_DIR, interval=1800, max_age=3600)
    )

    # ── Banner ────────────────────────────────────────────────────────────────
    port = int(os.getenv("PORT", "8080"))
    print(f"""
╔══════════════════════════════════════╗
║   IXO Multi-Platform Downloader Bot  ║
║   Mode:          polling             ║
║   Health port:   {port:<5}            ║
╚══════════════════════════════════════╝
""")

    # ── Always use polling (webhook mode removed for cloud simplicity) ─────────
    logger.info("Bot polling started.")
    await app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
