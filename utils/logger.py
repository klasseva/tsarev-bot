from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import colorlog


def setup_logger(name: str = "bot") -> logging.Logger:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)

    fmt_console = colorlog.ColoredFormatter(
        "%(log_color)s[%(asctime)s] [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt_console)
    logger.addHandler(sh)

    fh = RotatingFileHandler(log_dir / "bot.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    fh.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(fh)

    # discord internal
    logging.getLogger("discord").setLevel(logging.WARNING)
    return logger
