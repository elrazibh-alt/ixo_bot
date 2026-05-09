"""
Keyboard builders — keep all InlineKeyboardMarkup construction in one place.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def quality_keyboard(platform: str) -> InlineKeyboardMarkup:
    """Quality selection menu tailored per platform."""
    audio_platforms = {"soundcloud"}

    if platform in audio_platforms:
        # Audio-only platform: no quality choice needed
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎵 Download Audio", callback_data="q:audio")],
            [InlineKeyboardButton("❌ Cancel",         callback_data="cancel")],
        ])

    rows = [
        [
            InlineKeyboardButton("⬆️ Best Quality",  callback_data="q:best"),
            InlineKeyboardButton("🎵 Audio Only",    callback_data="q:audio"),
        ],
        [
            InlineKeyboardButton("📹 1080p",         callback_data="q:1080p"),
            InlineKeyboardButton("📹 720p",          callback_data="q:720p"),
            InlineKeyboardButton("📹 480p",          callback_data="q:480p"),
        ],
        [InlineKeyboardButton("❌ Cancel",           callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(rows)


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm",  callback_data="confirm")],
        [InlineKeyboardButton("❌ Cancel",   callback_data="cancel")],
    ])


def retry_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Retry", callback_data="retry")],
    ])
