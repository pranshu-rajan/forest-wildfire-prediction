"""
Centralised logging configuration for the forest-cover pipeline.

All modules import `get_logger(__name__)` to obtain a named logger that
writes structured messages to both the console and an optional rotating
file handler.  Credentials are never logged.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path


_LOG_DIR = Path("logs")
_DEFAULT_LEVEL = logging.INFO
_FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FMT = "%Y-%m-%dT%H:%M:%S"

_configured: bool = False


def setup_logging(
    level: int | str = _DEFAULT_LEVEL,
    log_file: str | Path | None = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 3,
) -> None:
    """Configure the root logger once per process.

    Parameters
    ----------
    level:
        Logging level (default INFO).  Can be an int or level name string.
    log_file:
        Optional path to a rotating log file.  Defaults to
        ``logs/pipeline.log`` when *None* and the ``logs/`` directory is
        writable.
    max_bytes:
        Maximum size (bytes) of the rotating log file before rollover.
    backup_count:
        Number of backup log files to keep.
    """
    global _configured
    if _configured:
        return

    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(_FMT, datefmt=_DATE_FMT)

    root = logging.getLogger()
    root.setLevel(level)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    root.addHandler(ch)

    # Optional file handler
    _log_file = log_file or (_LOG_DIR / "pipeline.log")
    try:
        Path(_log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.handlers.RotatingFileHandler(
            _log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        fh.setLevel(level)
        fh.setFormatter(formatter)
        root.addHandler(fh)
    except OSError:
        root.warning("Could not create log file at %s; console-only logging.", _log_file)

    # Suppress noisy third-party loggers
    for noisy in ("matplotlib", "PIL", "urllib3", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, ensuring logging is initialised.

    Usage::

        from python_src.logging_config import get_logger
        logger = get_logger(__name__)
    """
    if not _configured:
        setup_logging()
    return logging.getLogger(name)
