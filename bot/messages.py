"""
All user-facing message strings in one place.
Swap values here for multi-language support later.
"""

from core.base_downloader import MediaInfo

# ── Static messages ───────────────────────────────────────────────────────────

WELCOME = """
🤖 *IXO Multi-Platform Downloader*

Send me a video/audio link from any supported platform and I'll download it for you!

*Supported platforms:*
▸ Instagram (Reels, Posts, Stories, Carousels)
▸ TikTok
▸ YouTube & Shorts
▸ Twitter / X
▸ Facebook
▸ Reddit
▸ Pinterest
▸ Threads
▸ Vimeo
▸ SoundCloud
▸ Dailymotion
▸ And more!

/help — Usage guide
/platforms — Full platform list
"""

HELP = """
📖 *How to use*

1. Copy a video/audio link
2. Paste it here
3. Choose quality
4. Download!

*Quality options:*
• Best — highest available
• 1080p / 720p / 480p — specific resolution
• Audio only — MP3 audio

*Tips:*
• Public content only
• Max file size: 50 MB (Telegram limit)
• For large files, use audio-only mode
"""

PLATFORMS = """
📋 *Supported Platforms*

🎥 *Video*
Instagram • TikTok • YouTube
Twitter/X • Facebook • Threads
Vimeo • Dailymotion • Reddit

🎵 *Audio*
SoundCloud • YouTube (audio mode)

🖼 *Images*
Pinterest • Instagram posts

_More platforms added regularly!_
"""

RATE_LIMITED = "⏳ Too many requests. Please wait {seconds:.0f}s and try again."
UNSUPPORTED = "❌ Unsupported platform.\nSend /platforms to see what I support."
INVALID_URL = "❌ That doesn't look like a valid URL.\n\nPaste a full link starting with `https://`"
SESSION_EXPIRED = "⚠️ Session expired. Please send the link again."
TOO_LARGE = "❌ File is too large ({size_mb:.1f} MB). Telegram's limit is 50 MB.\n\nTry a lower quality or audio-only."
DOWNLOAD_FAILED = "❌ Download failed.\n\n{error}\n\nTry again or use a different link."
DOWNLOADING = "⏳ Downloading… please wait"
UPLOADING = "📤 Uploading ({size_mb:.1f} MB)…"
CANCELLED = "✅ Cancelled."


# ── Dynamic formatters ────────────────────────────────────────────────────────

def format_media_caption(info: MediaInfo) -> str:
    lines = []

    platform_emoji = {
        "instagram":   "📸",
        "tiktok":      "🎵",
        "youtube":     "▶️",
        "twitter":     "🐦",
        "facebook":    "👍",
        "reddit":      "🤖",
        "pinterest":   "📌",
        "threads":     "🧵",
        "vimeo":       "🎬",
        "soundcloud":  "☁️",
        "dailymotion": "📹",
    }.get(info.platform, "🔗")

    lines.append(f"{platform_emoji} *{_truncate(info.title, 60)}*")

    if info.uploader:
        lines.append(f"👤 @{info.uploader}")

    meta = []
    if info.duration:
        meta.append(f"⏱ {info.duration_str}")
    if info.view_count:
        meta.append(f"👁 {_format_num(info.view_count)}")
    if info.size_mb:
        meta.append(f"💾 {info.size_mb:.1f} MB")
    if meta:
        lines.append(" │ ".join(meta))

    if info.hashtags:
        lines.append(" ".join(info.hashtags[:5]))

    lines.append("_Downloaded by @IXO19BOT_")
    return "\n".join(lines)


def _truncate(text: str, n: int) -> str:
    return text if len(text) <= n else text[:n - 1] + "…"


def _format_num(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)
