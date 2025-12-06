from __future__ import annotations

import sys
from loguru import logger
from ssg_hs_forensics_app.core.config import get_config


# Loguru’s valid level names
_LOGURU_LEVELS = {
    "TRACE",
    "DEBUG",
    "INFO",
    "SUCCESS",
    "WARNING",
    "ERROR",
    "CRITICAL",
}


def init_logging(level: str | None = None) -> None:
    """
    Initialize Loguru with a merged-config or CLI override log level.
    Supports Loguru-specific levels: TRACE and SUCCESS.
    """

    # Determine effective log level
    if level:
        candidate = level.upper()
    else:
        cfg = get_config()
        candidate = cfg.get("application", {}).get("log_level", "INFO").upper()

    # Validate — if someone provides something invalid, default to INFO
    effective = candidate if candidate in _LOGURU_LEVELS else "INFO"

    # Reset handlers
    logger.remove()

    # Add clean stderr handler
    logger.add(
        sys.stderr,
        level=effective,
#        format="<green>{time}</green> | <level>{level}</level> | <level>{message}</level>",
        format="<level>{level:7}</level> | <level>{message}</level>",
        backtrace=False,
        diagnose=False,
    )

    logger.debug(f"Loguru initialized at level: {effective}")
