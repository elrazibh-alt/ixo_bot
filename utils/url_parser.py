"""
URL validation and platform detection.
Each platform is matched by its URL patterns — new platforms = add an entry to PLATFORM_PATTERNS.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Platform(str, Enum):
    INSTAGRAM  = "instagram"
    TIKTOK     = "tiktok"
    YOUTUBE    = "youtube"
    TWITTER    = "twitter"
    FACEBOOK   = "facebook"
    PINTEREST  = "pinterest"
    REDDIT     = "reddit"
    THREADS    = "threads"
    VIMEO      = "vimeo"
    SOUNDCLOUD = "soundcloud"
    SNAPCHAT   = "snapchat"
    DAILYMOTION= "dailymotion"
    LIKEE      = "likee"
    KWAI       = "kwai"
    UNKNOWN    = "unknown"


# Each entry: (Platform, list-of-regex-patterns)
PLATFORM_PATTERNS: list[tuple[Platform, list[str]]] = [
    (Platform.INSTAGRAM,  [r"instagram\.com/(reel|p|tv|stories)/",
                           r"instagr\.am/"]),
    (Platform.TIKTOK,     [r"tiktok\.com/@.+/video/",
                           r"vm\.tiktok\.com/",
                           r"vt\.tiktok\.com/"]),
    (Platform.YOUTUBE,    [r"youtube\.com/watch",
                           r"youtu\.be/",
                           r"youtube\.com/shorts/"]),
    (Platform.TWITTER,    [r"twitter\.com/.+/status/",
                           r"x\.com/.+/status/"]),
    (Platform.FACEBOOK,   [r"facebook\.com/.+/(videos|reel|watch)/",
                           r"fb\.watch/",
                           r"m\.facebook\.com/"]),
    (Platform.PINTEREST,  [r"pinterest\.(com|ca|co\.uk)/pin/",
                           r"pin\.it/"]),
    (Platform.REDDIT,     [r"reddit\.com/(r/.+/comments|gallery)/",
                           r"redd\.it/"]),
    (Platform.THREADS,    [r"threads\.net/@.+/post/"]),
    (Platform.VIMEO,      [r"vimeo\.com/\d+"]),
    (Platform.SOUNDCLOUD, [r"soundcloud\.com/.+/.+"]),
    (Platform.SNAPCHAT,   [r"snapchat\.com/spotlight/",
                           r"story\.snapchat\.com/"]),
    (Platform.DAILYMOTION,[r"dailymotion\.com/video/"]),
    (Platform.LIKEE,      [r"likee\.video/",
                           r"like\.video/"]),
    (Platform.KWAI,       [r"kwai\.com/",
                           r"kw\.ai/"]),
]


@dataclass
class ParsedURL:
    raw: str
    clean: str          # stripped of tracking params
    platform: Platform
    is_valid: bool
    error: Optional[str] = None


_TRACKING_PARAMS = re.compile(
    r"[?&](igsh|igshid|s|utm_source|utm_medium|utm_campaign|ref|fbclid)"
    r"=[^&]*",
    re.IGNORECASE,
)


def clean_url(url: str) -> str:
    """Remove common tracking / session query parameters."""
    url = url.strip()
    # Strip fragment
    url = url.split("#")[0]
    # Remove known tracking params
    url = _TRACKING_PARAMS.sub("", url)
    # Remove trailing ? or &
    url = url.rstrip("?&")
    return url


def detect_platform(url: str) -> Platform:
    for platform, patterns in PLATFORM_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return platform
    return Platform.UNKNOWN


def parse_url(raw: str) -> ParsedURL:
    """Validate and enrich a user-supplied URL."""
    if not raw or not raw.strip():
        return ParsedURL(raw=raw, clean="", platform=Platform.UNKNOWN,
                         is_valid=False, error="Empty URL")

    url = raw.strip()

    # Basic URL format check
    if not re.match(r"https?://", url, re.IGNORECASE):
        return ParsedURL(raw=raw, clean="", platform=Platform.UNKNOWN,
                         is_valid=False, error="URL must start with http:// or https://")

    cleaned = clean_url(url)
    platform = detect_platform(cleaned)

    if platform == Platform.UNKNOWN:
        return ParsedURL(raw=raw, clean=cleaned, platform=Platform.UNKNOWN,
                         is_valid=False,
                         error="Unsupported platform. Send /help to see supported sites.")

    return ParsedURL(raw=raw, clean=cleaned, platform=platform, is_valid=True)
