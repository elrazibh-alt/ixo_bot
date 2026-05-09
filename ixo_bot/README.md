# IXO Multi-Platform Downloader Bot 🤖

A production-ready Telegram bot that downloads videos, audio, and images from 13+ platforms — built with Python, asyncio, and yt-dlp.

---

## Features

| Category | Details |
|---|---|
| **Platforms** | Instagram, TikTok, YouTube, Twitter/X, Facebook, Reddit, Pinterest, Threads, Vimeo, SoundCloud, Dailymotion, and more |
| **Quality selection** | Best, 1080p, 720p, 480p, Audio-only |
| **Metadata** | Title, uploader, duration, views, hashtags |
| **Architecture** | Async, modular, one file per platform |
| **Concurrency** | Semaphore-limited parallel downloads |
| **Rate limiting** | Per-user sliding-window limiter |
| **Auto cleanup** | Background task removes old files |
| **Deployment** | Docker, Railway, Render, Koyeb, VPS, Fly.io |
| **Modes** | Polling (dev) + Webhook (production) |

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/you/ixo-bot.git
cd ixo-bot
pip install -r requirements.txt
```

> **Note:** `ffmpeg` must be installed on the system for yt-dlp to merge streams.
> - Ubuntu/Debian: `sudo apt install ffmpeg`
> - macOS: `brew install ffmpeg`

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set BOT_TOKEN
```

### 3. Run

```bash
python main.py
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_TOKEN` | ✅ | — | Telegram bot token from @BotFather |
| `WEBHOOK_URL` | ❌ | — | Full webhook URL; enables webhook mode when set |
| `WEBHOOK_PORT` | ❌ | `8443` | Port for webhook server |
| `MAX_FILE_SIZE_MB` | ❌ | `50` | Telegram upload limit |
| `MAX_CONCURRENT` | ❌ | `5` | Parallel downloads |
| `DOWNLOAD_TIMEOUT` | ❌ | `120` | Seconds before a download times out |
| `RETRY_COUNT` | ❌ | `3` | Retry attempts per download |
| `INSTAGRAM_COOKIES` | ❌ | — | Path to Netscape cookies file for Instagram |
| `YOUTUBE_COOKIES` | ❌ | — | Path to Netscape cookies file for YouTube |
| `LOG_LEVEL` | ❌ | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

---

## Docker

```bash
docker build -t ixo-bot .
docker run -e BOT_TOKEN=your_token ixo-bot
```

Or with Docker Compose:

```yaml
services:
  bot:
    build: .
    environment:
      BOT_TOKEN: your_token
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
```

---

## Deploy to Railway

1. Push repo to GitHub
2. Create new project on [railway.app](https://railway.app)
3. Set `BOT_TOKEN` in environment variables
4. Deploy — Railway detects the `Procfile` automatically

---

## Deploy to Render

1. Create a new Web Service
2. Connect your GitHub repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `python main.py`
5. Add `BOT_TOKEN` in Environment settings

---

## Project Structure

```
ixo-bot/
├── main.py                  # Entry point
├── config/
│   └── settings.py          # All config via env vars
├── bot/
│   ├── handlers.py          # Telegram handlers (commands, messages, callbacks)
│   ├── keyboards.py         # InlineKeyboardMarkup builders
│   └── messages.py          # User-facing strings and caption formatters
├── core/
│   ├── base_downloader.py   # Abstract base + MediaInfo dataclass
│   └── download_manager.py  # Dispatcher — routes URL to correct downloader
├── downloaders/
│   ├── instagram.py
│   ├── tiktok.py
│   ├── youtube.py
│   ├── twitter.py
│   └── generic.py           # Facebook, Reddit, Pinterest, Vimeo, SoundCloud, ...
├── utils/
│   ├── url_parser.py        # URL validation + platform detection
│   ├── rate_limiter.py      # Per-user sliding-window rate limiter
│   ├── cleanup.py           # File cleanup helpers + background task
│   └── logger.py            # Logging setup (console + rotating files)
├── logs/                    # Runtime log files (git-ignored)
├── downloads/               # Temp download directory (git-ignored)
├── .env.example
├── requirements.txt
├── Dockerfile
└── Procfile
```

---

## Adding a New Platform

1. Create `downloaders/myplatform.py` extending `BaseDownloader`
2. Implement `async def download(url, quality, download_dir) -> MediaInfo`
3. Add the platform to `utils/url_parser.py` → `PLATFORM_PATTERNS`
4. Register it in `core/download_manager.py` → `_register_downloaders()`

That's it — the router dispatches automatically.

---

## Using Cookies (for private/age-restricted content)

Export cookies from your browser using the [Get cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) extension and point the env var at the file:

```
INSTAGRAM_COOKIES=/app/config/instagram_cookies.txt
```

---

## License

MIT
