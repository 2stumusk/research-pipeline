"""Logging configuration with rotation support."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    log_file: Path,
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console: bool = True,
) -> logging.Logger:
    """Set up logging with rotation.

    Args:
        log_file: Path to log file
        level: Logging level
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        console: Whether to also log to console

    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger("research_pipeline")
    logger.setLevel(level)
    logger.handlers.clear()  # Clear any existing handlers

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler with rotation
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def cleanup_old_logs(log_dir: Path, days: int = 30) -> int:
    """Clean up log files older than specified days.

    Args:
        log_dir: Directory containing log files
        days: Number of days to keep

    Returns:
        Number of files deleted
    """
    import time
    from datetime import datetime, timedelta

    if not log_dir.exists():
        return 0

    cutoff = datetime.now() - timedelta(days=days)
    cutoff_timestamp = cutoff.timestamp()
    deleted = 0

    for log_file in log_dir.glob("*.log*"):
        if log_file.stat().st_mtime < cutoff_timestamp:
            try:
                log_file.unlink()
                deleted += 1
            except OSError:
                pass

    return deleted
