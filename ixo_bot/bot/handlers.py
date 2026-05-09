"""
Telegram bot handlers — commands, messages, callbacks.
"""

import logging
from pathlib import Path

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.keyboards import quality_keyboard, retry_keyboard
from bot.messages import (
    CANCELLED,
    DOWNLOADING,
    HELP,
    INVALID_URL,
    PLATFORMS,
    RATE_LIMITED,
    SESSION_EXPIRED,
    TOO_LARGE,
    UNSUPPORTED,
    UPLOADING,
    WELCOME,
    format_media_caption,
)
from config.settings import BotConfig
from core.base_downloader import MediaInfo
from core.download_manager import DownloadManager
from utils.cleanup import delete_file
from utils.rate_limiter import RateLimiter
from utils.url_parser import Platform, parse_url

logger = logging.getLogger(__name__)

# ── Module-level singletons (injected at startup) ─────────────────────────────
_settings: BotConfig
_manager: DownloadManager
_limiter: RateLimiter


def init_handlers(settings: BotConfig, manager: DownloadManager,
                  limiter: RateLimiter) -> None:
    global _settings, _manager, _limiter
    _settings = settings
    _manager  = manager
    _limiter  = limiter


def register(app) -> None:
    """Attach all handlers to the Application."""
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CommandHandler("platforms", cmd_platforms))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_url))
    app.add_handler(CallbackQueryHandler(on_callback))


# ── Commands ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME, parse_mode=ParseMode.MARKDOWN)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP, parse_mode=ParseMode.MARKDOWN)


async def cmd_platforms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(PLATFORMS, parse_mode=ParseMode.MARKDOWN)


# ── Message handler ───────────────────────────────────────────────────────────

async def on_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Rate limit check
    allowed, retry_after = await _limiter.is_allowed(user_id)
    if not allowed:
        await update.message.reply_text(
            RATE_LIMITED.format(seconds=retry_after),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Validate URL
    parsed = parse_url(text)
    if not parsed.is_valid:
        msg = INVALID_URL if parsed.platform == Platform.UNKNOWN and "http" not in text \
              else UNSUPPORTED
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        return

    # Store parsed URL for callbacks
    context.user_data["parsed_url"] = parsed

    await update.message.reply_text(
        f"✅ *{parsed.platform.value.title()} link detected!*\n"
        f"Select quality:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=quality_keyboard(parsed.platform.value),
    )


# ── Callback handler ──────────────────────────────────────────────────────────

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "cancel":
        await query.edit_message_text(CANCELLED)
        return

    if data.startswith("q:"):
        quality = data[2:]
        parsed = context.user_data.get("parsed_url")
        if not parsed:
            await query.edit_message_text(SESSION_EXPIRED)
            return
        context.user_data["quality"] = quality
        await _execute_download(query, context, parsed, quality)
        return

    if data == "retry":
        parsed  = context.user_data.get("parsed_url")
        quality = context.user_data.get("quality", "best")
        if not parsed:
            await query.edit_message_text(SESSION_EXPIRED)
            return
        await _execute_download(query, context, parsed, quality)
        return


# ── Download execution ────────────────────────────────────────────────────────

async def _execute_download(query, context, parsed, quality: str) -> None:
    await query.edit_message_text(DOWNLOADING, parse_mode=ParseMode.MARKDOWN)

    info: MediaInfo | None = None
    try:
        info = await _manager.download(parsed, quality)

        # Size check
        if info.file_size > _settings.MAX_FILE_SIZE:
            await query.edit_message_text(
                TOO_LARGE.format(size_mb=info.size_mb),
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        await query.edit_message_text(
            UPLOADING.format(size_mb=info.size_mb),
            parse_mode=ParseMode.MARKDOWN,
        )

        caption = format_media_caption(info)

        with open(info.file_path, "rb") as fh:
            if info.media_type == "audio":
                await query.message.reply_audio(
                    audio=fh,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    title=info.title,
                    performer=info.uploader,
                    duration=info.duration,
                )
            else:
                await query.message.reply_video(
                    video=fh,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    supports_streaming=True,
                    duration=info.duration,
                )

        await query.delete_message()

    except Exception as exc:
        logger.error("Download error for %s: %s", parsed.clean, exc, exc_info=True)
        await query.edit_message_text(
            f"❌ *Download failed*\n\n`{str(exc)[:200]}`\n\nTap Retry or send the link again.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=retry_keyboard(),
        )

    finally:
        # Always clean up temp file
        if info and info.file_path:
            await delete_file(info.file_path)
