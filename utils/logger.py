"""
Centralised logging setup.
Call setup_logging() once at startup; then use logging.getLogger(__name__) everywhere.
"""

import logging
import logging.handlers
import sys
from pathlib import Path


def setup_logging(log_dir: Path, level: str = "INFO", debug: bool = False) -> None:
    log_level = logging.DEBUG if debug else getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handlers: list[logging.Handler] = []

    # Console
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    handlers.append(console)

    # Rotating file — main log
    main_file = logging.handlers.RotatingFileHandler(
        log_dir / "bot.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    main_file.setFormatter(formatter)
    handlers.append(main_file)

    # Errors only
    error_file = logging.handlers.RotatingFileHandler(
        log_dir / "errors.log", maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    error_file.setLevel(logging.ERROR)
    error_file.setFormatter(formatter)
    handlers.append(error_file)

    logging.basicConfig(level=log_level, handlers=handlers, force=True)

    # Silence noisy third-party loggers
    for lib in ("httpx", "httpcore", "urllib3", "asyncio"):
        logging.getLogger(lib).setLevel(logging.WARNING)
