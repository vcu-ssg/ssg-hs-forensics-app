# src/ssg_hs_forensics_app/core/logger.py

"""
Singleton accessor for the global logger (Loguru), similar to get_config().

Use:
    from ssg_hs_forensics_app.core.logger import get_logger
"""

from __future__ import annotations

from functools import lru_cache
from loguru import logger as _logger

from ssg_hs_forensics_app.config_logger import init_logging


@lru_cache(maxsize=1)
def _initialize_logger(level_override: str | None = None):
    """
    Internal initializer. Ensures logging is initialized only once per process.
    """
    init_logging(level_override)
    return _logger


def get_logger(level_override: str | None = None):
    """
    Return the global Loguru logger.

    Parameters:
        level_override (str|None):
            Optional runtime override. If provided, forces re-init using this level.

    Behavior:
        • If level_override is None:
              Returns the cached logger (initialized on first call).
        • If level_override is provided:
              Reinitializes logging with new level and returns logger.
    """

    if level_override:
        # Clear cache, reinitialize with override
        _initialize_logger.cache_clear()
        return _initialize_logger(level_override)

    # Return already-initialized logger
    return _initialize_logger()
