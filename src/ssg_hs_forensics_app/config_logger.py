"""
Centralized Loguru initialization based on application config.

This module provides:
    • init_logging()  -> initialize Loguru according to config.toml
    • get_logger()    -> return the global logger (optional convenience)
"""

from __future__ import annotations

import sys
from loguru import logger

from ssg_hs_forensics_app.config_loader import load_builtin_config


# ============================================================
# Logging Initialization
# ============================================================

_initialized = False


def init_logging() -> None:
    """
    Initialize Loguru using settings from config.toml:

    [application]
    log_level = "DEBUG"

    Safe to call multiple times — only runs once.
    """
    global _initialized
    if _initialized:
        return

    cfg = load_builtin_config()
    app_cfg = cfg.get("application", {})
    level = app_cfg.get("log_level", "INFO").upper()

    # Remove default Loguru handler
    logger.remove()

    # Configure the new handler
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time}</green> | <level>{level}</level> | <level>{message}</level>",
    )

    logger.debug(f"Loguru initialized at level: {level}")
    _initialized = True


def get_logger():
    """Optional convenience method."""
    init_logging()
    return logger
