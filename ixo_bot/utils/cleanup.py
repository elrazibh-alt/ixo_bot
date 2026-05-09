"""
Async cleanup helpers — called after uploads and on a periodic schedule.
"""

import asyncio
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


async def delete_file(path: Path) -> None:
    """Delete a single file, silently ignore if missing."""
    try:
        if path and path.exists():
            path.unlink()
            logger.debug("Deleted: %s", path)
    except OSError as e:
        logger.warning("Could not delete %s: %s", path, e)


async def cleanup_old_files(directory: Path, max_age_seconds: int = 3600) -> int:
    """
    Remove files older than `max_age_seconds` from `directory`.
    Returns count of deleted files.
    """
    deleted = 0
    now = time.time()
    try:
        for f in directory.iterdir():
            if f.is_file() and (now - f.stat().st_mtime) > max_age_seconds:
                await delete_file(f)
                deleted += 1
    except OSError as e:
        logger.warning("Cleanup error in %s: %s", directory, e)
    return deleted


async def periodic_cleanup(directory: Path, interval: int = 1800,
                            max_age: int = 3600) -> None:
    """Background task: clean old downloads every `interval` seconds."""
    while True:
        await asyncio.sleep(interval)
        n = await cleanup_old_files(directory, max_age)
        if n:
            logger.info("Periodic cleanup: removed %d file(s)", n)
