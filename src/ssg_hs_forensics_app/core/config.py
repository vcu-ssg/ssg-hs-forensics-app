# src/ssg_hs_forensics_app/core/config.py

"""
Singleton accessor for merged configuration.
"""

from __future__ import annotations
from ssg_hs_forensics_app.config_loader import load_config


def get_config(config_file_override: str | None = None) -> dict:
    """
    Return merged config (built-in + user override OR custom override),
    cached for all callers.

    If config_file_override is provided, a fresh load occurs ignoring cache.
    """
    if config_file_override:
        # Bypass @lru_cache by calling with argument
        return load_config(config_file_override=config_file_override)

    # Normal cached load
    return load_config()
